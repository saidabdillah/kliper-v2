import sys, unittest, tempfile, subprocess, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studio import spans, captions, source, recommend, render, defaults
class Tests(unittest.TestCase):
 def test_cut(self):
  self.assertEqual(spans(2,9,[[5,7],[4,6]]),[(2,4),(7,9)])
 def test_time(self):
  s=captions([[2.2,2.5,"Halo"],[7.2,8,"Dunia"]],[(2,4),(7,9)],"srt")
  self.assertIn("00:00:02,200",s); self.assertNotIn("00:00:07,200",s)
 def test_url(self):
  for u in ["file:///etc/passwd","https://127.0.0.1/x.mp4","https://youtube.com.evil.test/watch?v=x","https://user@example.com/v.mp4"]:
   with self.assertRaises(ValueError): source(u)
 def test_moments(self):
  words=[[i,i+.4,"Kenapa?" if i%5==0 else "belajar."] for i in range(120)]
  clips=recommend(words,120,30); self.assertGreaterEqual(len(clips),3); self.assertTrue(all(c["end"]>c["start"] for c in clips))
 def test_render(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d); subprocess.run(["ffmpeg","-loglevel","error","-f","lavfi","-i","color=s=160x90:r=30:d=3","-f","lavfi","-i","sine=duration=3","-c:v","libx264","-threads","1","-c:a","aac",str(p/"source.mp4")],check=True)
   e=defaults(0,3); e["cuts"]=[[1,2]]; render(p,e,[[.1,.7,"Halo"],[2.1,2.7,"dunia"]],p/"out.mp4",[])
   meta=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(p/"out.mp4")]))["streams"]
   self.assertEqual((meta[0]["width"],meta[0]["height"]),(1080,1920)); self.assertAlmostEqual(float(meta[0]["duration"]),2,places=1); self.assertEqual(meta[1]["codec_name"],"aac")
