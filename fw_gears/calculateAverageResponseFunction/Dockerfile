# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM neurodebian:xenial
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY calculateAverageResponseFunction.py ${FLYWHEEL}/calculateAverageResponseFunction.py
RUN chmod +x /flywheel/v0/run

# Install required packages     
RUN apt-get update \
    && apt-get install -y \
    software-properties-common
RUN apt-get install -y \
    git \
    g++ \ 
    python \
    libeigen3-dev \
    zlib1g-dev \
    libqt5opengl5-dev \
    libqt5svg5-dev \ 
    libgl1-mesa-dev \
    libfftw3-dev \
    libtiff5-dev \
    libpng-dev \
    python3 \
    python3-pip \
    zip \
    unzip

# Install Mrtrix
RUN git clone https://github.com/MRtrix3/mrtrix3.git
RUN apt-get install libqt4-opengl-dev -y
RUN cd mrtrix3; ./configure; ./build

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run
