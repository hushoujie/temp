from PIL import Image
from ssis import SSIS, FONTS_PATH


def run():
    file_path = '/home/hsj/test1.jpg'
    ssis = SSIS()
    src_image = Image.open(file_path)
    mark_image = ssis.secret(src_image.size)
    dst_image = ssis.merge(src_image, mark_image)
    mark_image.show()
    dst_image.show()

if __name__ == '__main__':
    print(FONTS_PATH)
    run()