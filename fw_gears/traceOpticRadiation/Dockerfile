# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM neurodebian:xenial
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY extract_dti_values.py ${FLYWHEEL}/extract_dti_values.py
COPY fslinstaller.py /fslinstaller.py
RUN chmod +x /flywheel/v0/run
RUN chmod +x ${FLYWHEEL}/extract_dti_values.py

# Install required packages     
RUN apt-get update \
    && apt-get install -y \
    software-properties-common
RUN apt-get install -y \
    git \
    wget \
    g++ \ 
    python \
    python-pip \
    libeigen3-dev \
    zlib1g-dev \
    libqt5opengl5-dev \
    libqt5svg5-dev \ 
    libgl1-mesa-dev \
    libfftw3-dev \
    libtiff5-dev \
    libpng-dev \
    zip \
    ants \
    unzip

# Install python2 for fslinstallation and install the newest verison of fsl
RUN apt-get install python -y
RUN python2 /fslinstaller.py -d /fsl 

# Download and install Freesurfer on call
RUN wget https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.0/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.0.tar.gz
RUN mkdir freesurfer
RUN tar -zxf freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.0.tar.gz 
COPY license.txt /freesurfer/license.txt
ENV FREESURFER_HOME /freesurfer

# Install Mrtrix
RUN apt-get install libqt4-opengl-dev -y
RUN git clone https://github.com/MRtrix3/mrtrix3.git
RUN cd mrtrix3; ./configure; ./build

# Install trekker
RUN unzip trekker.zip
#RUN cd /trekker/; bash build_Linux.sh

# Install Anaconda
RUN apt-get install wget
RUN wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh
RUN bash Anaconda3-2020.02-Linux-x86_64.sh -b -p /anaconda3
ENV PATH=$PATH:/anaconda3/bin
RUN conda update --all -y

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run



