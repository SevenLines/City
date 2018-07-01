from back.base import app
import back.views as v

app.add_url_rule("/api/road/<qmin>/<qmax>/", view_func=v.RoadView.as_view("road"), methods=['GET'])
app.add_url_rule("/api/nearest-frame/", view_func=v.NearestFrameView.as_view("nearest-frame"), methods=['GET'])
app.add_url_rule("/api/multiline-defects/", view_func=v.MultilineDefectsView.as_view("multiline-defects"), methods=['GET'])
app.add_url_rule("/api/point-defects/", view_func=v.PointDefectsView.as_view("point-defects"), methods=['GET'])
app.add_url_rule("/photo/<path:path>", view_func=v.SendPhotoView.as_view("send-photo"), methods=['GET'])
