# This makes a container for the gear. Replace the first path next to the second COPY function 
# below with a path to your local compiled matlab function

FROM neurodebian:xenial
MAINTAINER Ozzy(ozenctaskin@hotmail.com)

#Copy everything into a container 
ENV FLYWHEEL /flywheel/v0/
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json run ${FLYWHEEL}
COPY create_fod_image.py ${FLYWHEEL}/create_fod_image.py
COPY ConstraintSet.mat ${FLYWHEEL}/ConstraintSet.mat
COPY sphere5120.obj ${FLYWHEEL}/sphere5120.obj
COPY adaptConOpt /tmp/adaptConOpt
COPY fslinstaller.py /fslinstaller.py

RUN chmod +x /flywheel/v0/run
RUN chmod +x ${FLYWHEEL}/create_fod_image.py

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

# Install python packages   
#RUN python3 -m pip install --upgrade pip
#RUN python3 -m pip install 'matplotlib==3.1.3' 'nibabel==2.5.1' 'numpy==1.18.1' 'imageio==2.8.0' 'nilearn==0.6.2' 'neuropythy==0.11.5' 'pandas==1.0.3' 'hcp-utils==0.1.0'

# Install Mrtrix
RUN apt-get install libqt4-opengl-dev -y
RUN git clone https://github.com/3Tissue/MRtrix3Tissue.git 
RUN cd MRtrix3Tissue; ./configure; ./build

# Download and install MCR on call
RUN apt-get install wget
RUN wget https://ssd.mathworks.com/supportfiles/downloads/R2020a/Release/5/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2020a_Update_5_glnxa64.zip
RUN mkdir matlabins
RUN unzip MATLAB_Runtime_R2020a_Update_5_glnxa64.zip -d /matlabins/
RUN /matlabins/install -mode silent -agreeToLicense yes

# Install python2 for fslinstallation and install the newest verison of fsl
RUN apt-get install python -y
RUN python2 /fslinstaller.py -d /fsl 

# Set the entrypoint  
ENTRYPOINT /flywheel/v0/run
