To build the docker image run this command, with the working directory being the directory of this README:
`docker build .`

To find the image id, look at the image list using:
`docker image list`

Using the most recently created docker image as the image ID:
`docker run -p 8080:8080 <image-id>`

The container should start with a web server running an individual client's CILViewer instance on 0.0.0.0:8080, and the listed docker IP address in the attached console.

To bind a directory with data on the host one could launch

`docker run -p 8080:8080 --mount type=bind,source="$(pwd)"/volume,target=/home/abc/bind <image-id> /home/abc/bind`
