import csv
import glob
import math
import os
from multiprocessing.pool import Pool
from subprocess import call

from back.base import db
from back.models import Frames, Video


def create_frame(frame):
    path = r"D:\_MMK\_PYTHON\CitySite\back\photo\{video_id}\frame_{id}.jpg".format(
        frame=frame['frame'],
        id=frame['id'],
        video_id=frame['video_id']
    )
    if os.path.exists(path):
        return False

    cmd = r'ffmpeg -i "{video_path}" -vf "select=eq(n\,{frame})" -vsync vfr -vframes 1 -y "{path}" -hide_banner'.format(
        video_path=frame['video_path'],
        frame=frame['frame'],
        path=path,
        id=frame['id']
    )
    call(cmd)
    return True


def main():
    frames = Frames.query.join(Frames.video).filter(Frames.done == False ).with_entities(
        Frames.id,
        Frames.frame,
        Video.path,
        Frames.video_id,
        Frames.idx
    )

    for video in Video.query.all():
        os.makedirs("D:\\_MMK\\_PYTHON\\CitySite\\back\\photo\\{video_id}\\".format(video_id=video.id), exist_ok=True )

    commands = []
    for f in frames:
        commands.append(dict(
            video_path=f.path,
            frame=f.frame,
            video_id=f.video_id,
            id=f.id
        ))
    pool = Pool(6)
    pool.map(create_frame, commands)


def main2():
    files = glob.glob(r'd:\_MMK\_ROADS\Roads-2018\САЙТ\Координаты 2018\*._sv')
    for f in files:
        with open(f) as file:
            reader = csv.reader(file, delimiter=';')
            for r in reader:
                f = Frames(
                    idx=r[0],
                    l=r[1],
                    x=r[2],
                    y=r[3],
                    z=r[4],
                    lng=math.degrees(float(r[5])),
                    lat=math.degrees(float(r[6])),
                    alt=r[7],
                    video_id=r[8],
                    frame=r[9],
                )
                db.session.add(f)
        db.session.commit()


if __name__ == '__main__':
    main()
