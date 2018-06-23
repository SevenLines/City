from flask import jsonify, request, send_from_directory
from flask.views import MethodView
from sqlalchemy import func

from back.base import db
from back.models import Frames


# @app.route()
# def send_photo(path):



class SendPhotoView(MethodView):
    def get(self, path, *args, **kwargs):
        return send_from_directory('photo', path)


class RoadView(MethodView):
    def get(self, *args, **kwargs):
        result = db.engine.execute('''
SELECT
  json_build_object(
      'type', 'Feature',
      'geometry', st_asgeojson(st_makeline(array_agg(st_makepoint(lat, lng) ORDER BY idx)))::json,
      'properties', json_build_object(
          'title', r.title,
          'video_id', video_id,
          'id', r.id
      )
  ) as data
FROM frames
  LEFT JOIN video v on frames.video_id = v.id
  LEFT JOIN roads r on v.road_id = r.id
GROUP BY r.title, r.id, video_id        
        ''')

        out = []
        for i in result:
            out.append(i.data)

        return jsonify({
            'objects': out
        })


class NearestFrameView(MethodView):
    def get(self, *args, **kwargs):
        lat = request.args['lat']
        lng = request.args['lng']
        video_id = request.args['video_id']

        frame = Frames.query.filter(Frames.video_id==video_id).order_by(
            func.st_distance(Frames.point, func.st_makepoint(lng, lat))
        )

        frame = frame.first()
        return jsonify({
            'url': '/photo/{}/frame_{}.jpg'.format(frame.video_id, frame.id),
            'position': frame.l,
            'frame': frame.frame,
        })
