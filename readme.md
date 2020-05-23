# conda + nginx + uwsgi运行配置说明
***

### 安装conda虚拟环境管理工具和运行环境
---

* 注：不用conda环境忽略此步,可以使用项目包中包含的pip导出的requirement.txt文件

* wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh
* chmod +x Miniconda3-***-.sh
* ./Miniconda3-***-.sh 按回车或yes
* source .bashrc
* 在~目录下会生成miniconda3文件夹，并且命令行开头出现base，安装成功
* vim 打开python3.6ForMark.yaml 按自己的路径修改最后一条记录，miniconda3/env/MarkDemo不要修改
* 运行 conda env create -f=/path/to/python3.6ForMark.yaml
* 运行 conda activate MarkDemo 进入环境
* 运行 python manege.py makemigrations
* 运行 python manege.py migrate
* 运行 python manage.py runserver 运行程序 若无无报错配置下一步，报错检查代码


### 安装配置运行uwsgi
---
* 退出虚拟环境
* 运行sudo apt install python3-pip
* 运行pip3 install uwsgi
* 运行uwsgi，打印uwsig帮助，安装成功
* 修改/path/to/project/Mark/Mark.ini 相关参数
* 运行uwsgi --ini /path/to/Mark.ini
* 运行 ps -aux | gerp uwsgi ,看到多个uwsgi进程，uwsgi启动成功

### 安装配置运行nginx
---
* apt install nginx
* sudo find / -name nginx 查找配置文件位置
* 取消默认配置
* 修改项目下的mark_nginx.conf 中相关配置
* 将修改后的配置copy到nginx.conf中
* nginx -t 检查nginx配置是否正确
* nginx -s reload 加载配置

### 部署注意事项
---
* 需要按需修改/path/to/project/Mark/Mark.ini中的socket，home，chdir参数，mark_nginx.conf中的server_name，static目录，media目录, uwsgi_pass参数, settings.py的HOST参数
* uwsgi中home选项可以指定conda虚拟环境或其他虚拟环境或真实环境
* 安装opencv-python时可能会未安装SMlib.6.0.so依赖包，导致运行Python manege.py runserver出错，ubuntu系统通过apt-file search SMlib.6.0.so 查找依赖并运行apt install <查到的名称> 安装