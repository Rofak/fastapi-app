

Run Development

uv run uvicorn app.main:app --reload

add whisper model

1-create folder whisper_model/small
2-copy downloaded small model to whisper_model/small 

▶️ 6. Run migration
alembic upgrade head


Celery redis
celery -A app.core.celery_app.celery worker --loglevel=info  
celery -A app.core.celery_app.celery worker --pool=solo --loglevel=info
celery -A app.core.celery_app.celery flower --port=5555


ffmpeg -i a.wav -i b.wav -filter_complex " 
[0:a]asetpts=PTS-STARTPTS,aresample=44100,atempo=2,adelay=9420|9420[a0]; 
[1:a]asetpts=PTS-STARTPTS,aresample=44100,atempo=1.5,adelay=10100|10100[a1]; 
[a0][a1]amix=inputs=2[aout] " -map "[aout]" output.wav


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

ffmpeg -y -i "https://sin1.contabostorage.com/f3dc5ccef6ea4e62b8fa33db51a4c53d:public/AITools/Chinese Short Films.mp4" -i "a_0.wav" -i "a_1.wav" -filter_complex "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,aresample=44100,atempo=1.25,adelay=9420|9420[a1];[2:a]aformat=sample_rates=44100:channel_layouts=stereo,aresample=44100,atempo=0.85,adelay=10100|10100[a2];[0:a]aformat=sample_rates=44100:channel_layouts=stereo,aresample=44100[a0];[a0][a1][a2]amix=inputs=3:duration=longest:dropout_transition=0:normalize=0,volume=2[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest output_video.mp4