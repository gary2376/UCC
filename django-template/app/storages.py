from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    bucket_name = 'aws.bucket.name'
    custom_domain = 'aws.bucket.url'
    isfilecached = {}
