# Use an nginx base image
FROM nginx:alpine

#Removing the default Nginx static files
RUN rm -rf /usr/share/nginx/html/*

#Copying the frontend files into Nginx's static directory
COPY . /usr/share/nginx/html/

#Exposing port 80 to the host
EXPOSE 80

#Start Nginx in the foreground
CMD ["nginx","-g","daemon off;"]