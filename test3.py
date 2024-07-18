import gdown
# import tarfile 
url = 'https://drive.google.com/uc?id=1MjDsCOUqatdNvLDuQyJHNWI35cd46WXN'
# "https://drive.google.com/file/d/1li-GFm-Pvc7VSKYPD8FRRWAV6GdydW1e/view?usp=sharing"
output = "./model/model-00002-of-00002.safetensors"
gdown.download(url, output, quiet=False)

# file = tarfile.open('model') 
# file.extractall('./model') 

# file.close() 