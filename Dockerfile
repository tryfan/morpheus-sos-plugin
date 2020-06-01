FROM centos:7
MAINTAINER tryfan@celebic.net

RUN yum -y install rpm-build python-setuptools

RUN mkdir /dist
VOLUME /dist

ADD . /source
WORKDIR /source

RUN python setup.py bdist_rpm

CMD ["bash", "-c", "cp -f /source/dist/*.rpm /dist"]