FROM fedora:29
RUN dnf -y install python3
RUN pip3 install selenium
