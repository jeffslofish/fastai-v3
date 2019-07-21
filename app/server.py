import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
import re
from environs import Env
import os
from pathlib import Path

env = Env()
env.read_env()
# Get export_file_url from environment variable. If its not there, look in .env file
export_file_url = os.getenv("EXPORT_FILE_URL")
if (export_file_url is None):
    print("can not find export_file_url")
    env('EXPORT_FILE_URL')
else:
    export_file_url = export_file_url[3:len(export_file_url) - 3]
    print(export_file_url)
export_file_name = 'export.pkl'

classes = ['bash', 'c', 'c#', 'c++', 'css', 'haskell', 'html', 'java', 'javascript', 'lua', 'markdown', 'objective-c', 'perl', 'php', 'python', 'r', 'ruby', 'scala', 'sql', 'swift', 'vb.net']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    formData = await request.form()
    bytesRead = await (formData['file'].read())
    prediction = learn.predict(bytesRead)
    m = re.search('\(Category ([\.\+\#\-\w]+), ', str(prediction))
    language = "Error"
    if (m is not None):
        language = m.group(1)
    return JSONResponse({'result': str(language)})

if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
