/ref: https://stackoverflow.com/questions/35222732/securing-mongo-when-in-docker-container
echo "=> Creating an ${MONGO_USERNAME} user for ${MONGO_INITDB_DATABASE} in MongoDB"

mongo admin -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD << EOF
use admin
db.createUser({
    user: '$MONGO_USERNAME', 
    pwd: '$MONGO_PASSWORD', 
    roles:[{role:'readWrite',db:'$MONGO_INITDB_DATABASE'}]
})
EOF