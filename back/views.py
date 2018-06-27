from rapidjson import dumps

from flask import jsonify, request, send_from_directory
from flask.views import MethodView
from sqlalchemy import func, and_

from back.base import db, cache, app
from back.models import Frames, RoadQuality, Roads

@cache.memoize(5000)
def get_quality_info(qmin, qmax):
    result = db.engine.execute('''
SELECT 
  json_build_object(
      'type', 'Feature',
      'properties', json_build_object(
          'score', LEAST(5, coalesce(score, 5)),
          'road_id', r.id,
          'rq_id', rq.id,
          'video_id', f.video_id,
          'start', rq.start,
          'end', rq.end
      ),
      'geometry', st_asgeojson(st_collect(st_makeline(f.point, f2.point)))::json
  ) as data
FROM frames f
  LEFT JOIN frames f2 ON f2.idx + 1 = f.idx and f.video_id = f2.video_id
  LEFT JOIN video v ON v.id = f.video_id
  LEFT JOIN roads r ON r.id = v.road_id
  LEFT JOIN road_quality rq ON rq.road_id = v.road_id and f.l >= rq.start and f.l <= rq.end
WHERE f2.idx is not NULL and LEAST(5, coalesce(score, 5)) between {} and {}
GROUP BY LEAST(5, coalesce(score, 5)), defects, r.id, rq.start, rq.end, f.video_id, rq.id
        '''.format(qmin, qmax))

    out = []
    for i in result:
        out.append(i.data)

    return out


class SendPhotoView(MethodView):
    def get(self, path, *args, **kwargs):
        return send_from_directory('photo', path)


class RoadView(MethodView):
    def get(self, qmin, qmax, *args, **kwargs):
        roads_list = {str(i.id): i.title for i in Roads.query.all()}
        quality_info = get_quality_info(float(qmin), float(qmax))

        respons_content = dumps({
            'roads': quality_info,
            'roads_list': roads_list,
        })
        response = app.response_class(respons_content, mimetype=app.config['JSONIFY_MIMETYPE'])

        return response


class PointDefectsView(MethodView):
    def get(self, *args, **kwargs):
        types = list(map(str, map(int, request.args.getlist('filters[]'))))

        out = []
        if types:

            query = """
    SELECT
      json_build_object(
               'type', 'Feature',
               'geometry', st_asgeojson(st_makepoint(
                      52.28309999999998 + y * -8.986642677244117e-06,
                      104.30060000000013 + x * -1.4655401709054041e-05
                  )
               )::json,
               'properties', json_build_object(
                   'road_id', road_id,
                   'type', pd."type",
                   'l', pd.address,
                   'defects', pd.defect_types_id
               )
           ) as data
    FROM point_defects pd
    LEFT JOIN roads r on pd.road_id = r.id
            """
            query += " WHERE defect_types_id && ARRAY[{}]".format(",".join(types))

            result = db.engine.execute(query)

            for i in result:
                out.append(i.data)

        return jsonify({
            'defects': out
        })

class NearestFrameView(MethodView):
    def get(self, *args, **kwargs):
        lat = request.args['lat']
        lng = request.args['lng']
        video_id = request.args['video_id']
        rq_id = request.args.get('rq_id')

        if rq_id:
            rq = RoadQuality.query.filter_by(id=rq_id).first()
        frame = Frames.query.filter(Frames.video_id==video_id).order_by(
            func.st_distance(Frames.point, func.st_makepoint(lng, lat))
        )

        frame = frame.first()
        return jsonify({
            'url': '/photo/{}/frame_{}.jpg'.format(frame.video_id, frame.id),
            'position': frame.l,
            'frame': frame.frame,
            'defects': rq.defects if rq_id else 'дефекты отсутствуют',
            'score': rq.score if rq_id else '5',
        })


class QualityView(MethodView):
    def get(self):
        low = float(request.args.get('low', 0))
        high = float(request.args.get('high', 5))

        query = """
SELECT
  json_build_object(
      'type', 'Feature',
      'properties', json_build_object(
          'defects', defects,
          'score', LEAST(5, coalesce(score, 5)),
          'road', r.title,
          'video_id', f.video_id,
          'start', rq.start,
          'end', rq.end
      ),
      'geometry', st_asgeojson(st_collect(st_makeline(f.point, f2.point)))
  ) as data
FROM frames f
  LEFT JOIN frames f2 ON f2.idx + 1 = f.idx and f.video_id = f2.video_id
  LEFT JOIN video v ON v.id = f.video_id
  LEFT JOIN roads r ON r.id = v.road_id
  LEFT JOIN road_quality rq ON rq.road_id = v.road_id and f.l > rq.start and f.l < rq.end
WHERE f2.idx is not NULL
GROUP BY LEAST(5, coalesce(score, 5)), defects, r.title, rq.start, rq.end, f.video_id 
"""
        result = db.engine.execute(query)
        out = []
        for i in result:
            out.append(i.data)

        return jsonify({
            'quality_info': out
        })