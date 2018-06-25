from flask import jsonify, request, send_from_directory
from flask.views import MethodView
from sqlalchemy import func

from back.base import db
from back.models import Frames


class SendPhotoView(MethodView):
    def get(self, path, *args, **kwargs):
        return send_from_directory('photo', path)


class RoadView(MethodView):
    def get(self, *args, **kwargs):
        result = db.engine.execute('''
SELECT
  json_build_object(
      'type', 'Feature',
      'properties', json_build_object(
          'score', LEAST(5, coalesce(score, 5)),
          'road_title', r.title,
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
  LEFT JOIN road_quality rq ON rq.road_id = v.road_id and f.l > rq.start and f.l < rq.end
WHERE f2.idx is not NULL
GROUP BY LEAST(5, coalesce(score, 5)), defects, r.title, rq.start, rq.end, f.video_id, rq.id      
        ''')

        out = []
        for i in result:
            out.append(i.data)

        return jsonify({
            'roads': out
        })


class NearestFrameView(MethodView):
    def get(self, *args, **kwargs):
        lat = request.args['lat']
        lng = request.args['lng']
        video_id = request.args['video_id']

        frame = Frames.query.filter(Frames.video_id==video_id).join(

        ).order_by(
            func.st_distance(Frames.point, func.st_makepoint(lng, lat))
        )

        frame = frame.first()
        return jsonify({
            'url': '/photo/{}/frame_{}.jpg'.format(frame.video_id, frame.id),
            'position': frame.l,
            'frame': frame.frame,
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