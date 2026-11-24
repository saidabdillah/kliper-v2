import json, subprocess, tempfile, unittest
from pathlib import Path
from studio import STYLES,SIZES,defaults,render

class RenderFormats(unittest.TestCase):
 def test_six_rendered_styles_three_dimensions_and_frame_rates(self):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=black:s=320x180:r=60:d=1','-f','lavfi','-i','sine=duration=1','-c:v','libx264','-threads','1','-c:a','aac',str(p/'source.mp4')],check=True)
        for i,s in enumerate(STYLES):
            ratio=list(SIZES)[i%3];fps=[30,60][i%2];e=dict(defaults(0,.5),style=s,ratio=ratio,fps=fps);out=p/'clip.mp4'
            with self.subTest(style=s,ratio=ratio,fps=fps):
                render(p,e,[[.01,.45,'Kenapa?']],out,[[0,.5]]);track=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(out)]))['streams'][0];self.assertEqual((track['width'],track['height']),SIZES[ratio]);self.assertEqual(track['r_frame_rate'],f'{fps}/1');raw=subprocess.check_output(['ffmpeg','-loglevel','error','-ss','0.2','-i',str(out),'-frames:v','1','-vf','scale=240:-2,format=gray','-threads','1','-f','rawvideo','-']);self.assertGreater(max(raw),60,'No visible subtitle pixels on black source')
