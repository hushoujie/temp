import random
import string
from copy import deepcopy
import os
import operator

from PIL import Image

from rest_framework.response import Response
from rest_framework import views
from rest_framework import status

from Mark.settings import MEDIA_ROOT, MEDIA_URL, HOST

from utils.luckyen.copyright.watermark.image.ssis import SSIS
from utils.luckyen.copyright.similarity.image.entropy import EntropySimilarity


# Create your views here.


def create_random_str(num=10):
    return ''.join(random.choice(string.digits) for _ in range(num))


def get_max_score(score_dict):
    score_dict = sorted(score_dict.items(), key=operator.itemgetter(1))[0]
    return score_dict


def get_all_marked_image_name(path=MEDIA_ROOT):
    names = os.listdir(path)
    for name in names:
        if 'marked' not in name:
            names.remove(name)
    names = ['{path}{name}'.format(path=path, name=name) for name in names]
    return names


class EncodeAPIView(views.APIView):

    def post(self, request, *args, **kwargs):

        if request.data.get('src_image') is None:
            return Response({"code":1, "msg":'src_image字段不能为空'},status=status.HTTP_400_BAD_REQUEST)
        image_file = request.data.get('src_image')
        random_str = create_random_str()
        src_file_path = '{media_root}src_{id}.jpg'.format(media_root=MEDIA_ROOT, id=random_str)
        with open(src_file_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)
        file_path_list = list()
        download_list = list()
        for i in range(3):
            file_name = 'marked_{id}.jpg'.format(id=create_random_str())
            file_path_list.append('{media_root}{file_name}'.format(media_root=MEDIA_ROOT, file_name=file_name))
            download_list.append(
                '{host}{media_url}{file_name}'.format(host=HOST, media_url=MEDIA_URL, file_name=file_name))
        src_image_data = Image.open(src_file_path)
        ssis = SSIS()
        for file_path in file_path_list:
            mark_image = ssis.secret(src_image_data.size)
            ssis.merge(deepcopy(src_image_data), mark_image).save(file_path, format='JPEG', subsampling=0, quality=100)

        download_dict = [{"download": item} for item in download_list]

        data = {"code": 0,
                "msg": "成功",
                "data": {"downloadlist": download_dict}
                }
        return Response(data=data, status=status.HTTP_200_OK)


class DecodeAPIView(views.APIView):

    def post(self, request, *args, **kwargs):
        if request.data.get('marked_image') is None:
            return Response({"code":1, "msg":'marked_image字段不能为空'},status=status.HTTP_400_BAD_REQUEST)
        file = request.data.get('marked_image')
        file_path = '{media_root}temp.jpg'.format(media_root=MEDIA_ROOT)
        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        names = get_all_marked_image_name(path=MEDIA_ROOT)
        score_dict = dict()
        for name in names:
            score = EntropySimilarity(file_path).compare(name)
            score_dict.__setitem__(name, score)
        _id, score = get_max_score(score_dict)
        id = str(_id).split('_')[-1].split('.')[0]

        data = {"code": 0,
                "msg": "成功",
                "data": {
                    "id": id,
                    "score": str(score)
                }
                }
        if os.path.exists(file_path):
            os.remove(file_path)
        return Response(data=data, status=status.HTTP_200_OK)
