FROM debian:latest

WORKDIR /collector
ENV VIRTUAL_ENV="$WORKDIR/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update \
	&& apt-get install -y \
	python3 python3-venv python3-pip \
	&& apt-get clean


# TEMPORARY INSTALL
#RUN apt-get install -y netcat telnet net-tools
# TEMPORARY INSTALL


#RUN python3 -m pip install --upgrade pip
RUN python3 -m venv $VIRTUAL_ENV
RUN . $VIRTUAL_ENV/bin/activate

# Install dependencies:
ADD requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application
RUN mkdir functions
RUN mkdir config
ADD functions functions
ADD main.py .

# Run the application:
CMD ["python3", "main.py"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]
