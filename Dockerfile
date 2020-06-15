FROM centos:7
MAINTAINER tryfan@celebic.net

RUN yum -y install rpm-build python-setuptools

RUN mkdir /dist
VOLUME /dist

ADD . /source
WORKDIR /source

ARG argrelnum=1

ENV relnum $argrelnum

RUN python setup.py bdist_rpm --release $relnum

CMD ["bash", "-c", "cp -f /source/dist/*.rpm /dist"]