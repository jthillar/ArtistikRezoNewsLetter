
import os
import credentials


SECRET_KEY = '@;cHa]d#]j)t9XKd(-2pA7#y'

cd = credentials.GetCredentials('passwordARNL.kdbx', os.environ['PASSWORD'])
MONGO_URI = "mongodb+srv://" + cd.mongoDbUsername() + ":" + cd.mongoDbPassword() + cd.mongoDbUrl()
MONGO_DBNAME = 'artistik_rezo'