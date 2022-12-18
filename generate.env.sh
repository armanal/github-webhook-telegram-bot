if ! command -v pwgen &> /dev/null
then
    echo "pwgen not found. installing pwgen."
    apt update && \
    apt install -y pwgen
fi


echo TOKEN=\"\" > .env
echo MONGO_SERVER=mongodb >> .env
echo MONGODB_PORT=27227 >> .env
echo MONGO_INITDB_DATABASE=\'gwhtb\' >> .env
echo MONGO_INITDB_ROOT_USERNAME=\'admin\' >> .env
echo MONGO_INITDB_ROOT_PASSWORD=\"$(pwgen 32 1)\" >> .env
echo MONGO_USERNAME=\'github\' >> .env
echo MONGO_PASSWORD=\"$(pwgen 32 1)\" >> .env
echo URL=\"\" >> .env
echo "Created .env file"