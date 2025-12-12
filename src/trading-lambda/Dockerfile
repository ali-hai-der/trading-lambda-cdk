FROM public.ecr.aws/lambda/python:3.11

# Install build dependencies needed for compiling numpy
# Install gcc-toolset-9 which provides GCC 9.3+ required by numpy 2.x
RUN yum install -y gcc-toolset-9 gcc-toolset-9-gcc gcc-toolset-9-gcc-c++ python3-devel && \
    yum clean all

# Enable gcc-toolset-9 for the build
ENV PATH="/opt/rh/gcc-toolset-9/root/usr/bin:$PATH"
ENV CC="/opt/rh/gcc-toolset-9/root/usr/bin/gcc"
ENV CXX="/opt/rh/gcc-toolset-9/root/usr/bin/g++"

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY methods/ ${LAMBDA_TASK_ROOT}/methods/
COPY aws/ ${LAMBDA_TASK_ROOT}/aws/
COPY constants.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "handler.handler" ]
