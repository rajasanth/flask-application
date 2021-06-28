from flask import Flask, render_template, request, redirect, url_for
import os, json, boto3
import logging, sys
import botocore
from botocore.client import Config

app = Flask(__name__)

#@app.route('/', methods = ['GET'])
#def healthcheck():
 #  return FlaskResponse(status=200) 

@app.route('/files/download/', methods = ['GET'])
def create_presigned_url():
    """Generate a presigned URL to share an S3 object
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))
    try:
        key = request.args.get('key')
        key_prefix = os.environ.get('KEY_PREFIX', "")
        if (key_prefix is not None):
          print("key_prefix exists...", key_prefix)
          key = key_prefix + "/" + key
        
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': os.environ.get('BUCKET_NAME'),
                                                            'Key': key})
    except botocore.exceptions.ClientError as e:
        return None

    # The response contains the presigned URL
    return response

@app.route('/files/upload/', methods = ['POST'])
def fileUpload():
  logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
  try:
    logging.debug("Entering Upload method")
    bucket_name = os.environ.get('BUCKET_NAME')
    print("The value of bucket name is..", bucket_name)
    #fileName=request.form['fileName']  
    #print("The value of filename is..", fileName)
    name = None
    fileNames = None
    for keys in request.files.keys():
      logging.debug("printing the keys ", keys)
      fileNames = keys
      name = request.files[keys]
    s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))  
    #s3_resource = boto3.resource('s3', verify=False)
    
    #fileName = request.args.get('fileName')
    
    #key = request.args.get('key')
    key = os.environ.get('KEY_PREFIX')
    if (key is not None):
      logging.debug("key_prefix exists...", key)
      key = key + "/" + name.filename
    else:
      logging.debug("key_prefix doesnt exist")
      key = name.filename
    if (IsBucketExists (bucket_name)):
      s3_client.upload_fileobj(name, bucket_name, key)
      #s3_resource.Bucket(bucket_name).upload_file(Filename=name.filename, Key=key)
  except botocore.exceptions.ClientError as error:
    raise error
  #return Flask.Response(status=200)  
  return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

def IsBucketExists(bucket_name):
  try:
    s3_resource = boto3.resource('s3', verify=False)
    s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    print("Bucket exists..", bucket_name)
    exists = True
  except botocore.exceptions.ClientError as error: 
    error_code = int(error.response['Error']['Code'])
    if error_code == 403:
      print("Private Bucket. Forbidden Access! ", bucket_name)
      raise error
    elif error_code == 404:
      print("Bucket Does Not Exist!", bucket_name)
      raise error
    exists = False
  return exists     
         

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port = port, debug = True)
