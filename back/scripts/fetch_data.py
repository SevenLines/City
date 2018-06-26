import csv
import glob
import json
import math
import os
from multiprocessing.pool import Pool
from subprocess import call

from back.base import db, app
from back.models import Frames, Video, RoadQuality, PointDefects


def create_frame(frame):
    cmd = r'ffmpeg -i "{video_path}" -vf "select=eq(n\,{frame})" -vsync vfr -vframes 1 -y "{path}" -hide_banner'.format(
        video_path=frame['video_path'],
        frame=frame['frame'],
        path=frame['path'],
        id=frame['id']
    )
    print(cmd)
    try:
        call(cmd)
    except:
        return False
    return True


def create_frames(ids=None):
    if ids is None:
        ids = []

    frames = Frames.query.join(Frames.video)\
        .with_entities(
        Frames.id,
        Frames.frame,
        Video.path,
        Frames.video_id,
        Frames.idx
    )

    if ids:
        frames = frames.filter(Frames.video_id.in_(ids))

    for video in Video.query.all():
        os.makedirs("D:\\_MMK\\_PYTHON\\CitySite\\back\\photo\\{video_id}\\".format(video_id=video.id), exist_ok=True )

    commands = []
    for f in frames:
        path = r"D:\_MMK\_PYTHON\CitySite\back\photo\{video_id}\frame_{id}.jpg".format(
            frame=f.frame,
            id=f.id,
            video_id=f.video_id
        )
        if os.path.exists(path):
            return False

        commands.append(dict(
            path=path,
            video_path=f.path,
            frame=f.frame,
            video_id=f.video_id,
            id=f.id
        ))
    pool = Pool(6)
    pool.map(create_frame, commands)

    db.engine.execute("""
UPDATE frames
SET point = st_makepoint(lat, lng)    
    """)


def fill_frames():
    files = glob.glob(r'd:\_MMK\_ROADS\Roads-2018\САЙТ\Координаты 2018\Кадры ул. Шевцова, г. Иркутск._sv')
    video_ids = set()
    for f in files:
        with open(f) as file:
            reader = csv.reader(file, delimiter=';')
            for r in reader:
                try:
                    f = Frames(
                        idx=r[0],
                        l=r[1],
                        x=r[2],
                        y=r[3],
                        z=r[4],
                        lng=math.degrees(float(r[5])),
                        lat=math.degrees(float(r[6])),
                        alt=r[7],
                        video_id=r[34],  # 8,9 прямое, 34,35 -- обратное
                        frame=r[35],
                    )
                    video_ids.add(f.video_id)
                    db.session.add(f)
                except:
                    pass
        db.session.commit()
        print(video_ids)
    return video_ids


def find_frames_without_images():
    sql = """
SELECT DISTINCT ON (r.title, v.id) r.title, v.id as video_id, f.id as id
FROM frames f
  LEFT JOIN video v on f.video_id = v.id
  LEFT JOIN roads r on v.road_id = r.id    
    """
    frames = db.engine.execute(sql)
    for f in frames:
        path = os.path.join(app.root_path, 'photo/{}/frame_{}.jpg'.format(f.video_id, f.id))
        if not os.path.exists(path):
            print(f)


def quality_info():
    files = glob.glob(r'd:\_MMK\_PYTHON\CityDiagnostics\out\json\*.json')
    for f in files:
        with open(f) as fl:
            data = json.loads(fl.read())
            road_id = list(data.keys())[0]
            for q in data[road_id]['quality']:
                rq = RoadQuality(
                    road_id=road_id,
                    start=q['pos'],
                    end=q['pos'] + q['length'],
                    defects=q['defects'],
                    score=q['score'],
                )
                db.session.add(rq)
        db.session.commit()


def load_point_defects():
    files = glob.glob(r'd:\_MMK\_PYTHON\CityDiagnostics\out\json\*.json')
    for f in files:
        with open(f) as fl:
            data = json.loads(fl.read())
            road_id = list(data.keys())[0]
            for q in data[road_id]['bad_wheels']:
                pd = PointDefects(
                    road_id=road_id,
                    x=q['x'],
                    y=q['y'],
                    address=q['l'],
                    type=q['type'],
                    defects=q['defects'],
                )
                db.session.add(pd)
            for q in data[road_id]['trails']:
                t = PointDefects(
                    road_id=road_id,
                    x=q['x'],
                    y=q['y'],
                    address=q['start'],
                    type=q['type'],
                    defects=q['defect'],
                )
                db.session.add(t)
        db.session.commit()


if __name__ == '__main__':
    load_point_defects()
    # video_ids = fill_frames()
    # if video_ids:
    #     create_frames(video_ids)
