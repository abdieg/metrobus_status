# Automatically stop and delete old container to create and run the new one
docker rm -f metrobus_estado 2>/dev/null || true && \
docker run -d --name metrobus_estado --restart unless-stopped --network ntfy_default metrobus_scrapper
