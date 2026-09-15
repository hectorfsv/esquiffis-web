#!/usr/bin/env python3
"""Put VaderClawd into the Esquiffis web page.

    python3 tools/build-pet.py

Takes the desktop pet's own code (../vader-clawd-pet/src/pet-shell.html) with the Render Rig's
sprites and engine spliced in exactly as the pet's build does (../render-rig/index.html, between
the `sprites` and `lifecycle` markers), applies the WEB patches below, and writes the result into
index.html between /*VADERCLAWD-BEGIN*/ and /*VADERCLAWD-END*/. Re-run after the pet or rig changes.

Web patches (Hector 2026-09-14):
  - roam only: never a show, never walks off the page
  - mostly stays where he is; now and then he crosses to another part of the page
  - big moves more often (drones, probe, swarm, flyover, workout, a crate); no climbing
  - no night meditation, no CPU sign, no march, no sound
  - lines about Esquiffis, and pet.react(kind) so the page can make him react to replies
  - the loop starts on a timer, not requestAnimationFrame (works in a background tab and headless)
The pet and the rig are NOT modified."""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
PROJ = HERE.parent
rig = (PROJ / 'render-rig/index.html').read_text()
shell = (PROJ / 'vader-clawd-pet/src/pet-shell.html').read_text()

a, b = '/* ---------- sprites ---------- */', '/* ---------- lifecycle ---------- */'
assert rig.count(a) == 1 and rig.count(b) == 1, 'rig markers moved'
engine = rig[rig.index(a):rig.index(b)]
m = re.search(r'<script>\n(.*)\n</script>', shell, re.S)
assert m, 'pet shell script not found'
js = m.group(1)
assert js.count('/*__ENGINE__*/') == 1
js = js.replace('/*__ENGINE__*/', engine)


def once(s, old, new):
    n = s.count(old)
    assert n == 1, 'patch target found %d times: %r' % (n, old[:70])
    return s.replace(old, new)


def once_re(s, pat, new):
    out, n = re.subn(pat, lambda _m: new, s, flags=re.S)
    assert n == 1, 'patch pattern matched %d times: %r' % (n, pat[:70])
    return out


js = once(js, "document.getElementById('cv')", "document.getElementById('vc-cv')")
js = once(js, "host=document.getElementById('stage')", "host=document.getElementById('vc-stage')")
js = once(js, "var opts={night:true,sound:false,bubbles:true,climb:true,march:true,",
              "var opts={night:false,sound:false,bubbles:true,climb:false,march:false,")
js = once(js, "fps:30,skip:true,sign:true};", "fps:30,skip:true,sign:false};")

# roam only
js = once(js, "    if(away||was==='roam') return play(pick());\n    play('roam');",
              "    play('roam');   // WEB: never a show")
js = once_re(js, r"      if\(Math\.random\(\)<\.3\)\{\s+// a full show: he walks off and it plays\n.*?mode='exit'; return; \}\n", "")

# he walks in from the RIGHT and settles where the page says he can be seen (window.PET_HOME / PET_PICK):
# outside the card on the right, free to cross behind it to the left (Hector 2026-09-14)
js = once(js, "var sp=spd(),V=new Actor('vader',-44*S,1),t=0,mode='walk',", "var sp=spd(),V=new Actor('vader',W+10*S,-1),t=0,mode='walk',")
js = once(js, "walk(V,W*(.15+Math.random()*.3),sp*(isNight()?.6:1));",
              "walk(V,(function(){ try{ var h=window.PET_HOME&&window.PET_HOME(W,S); if(isFinite(h)) return h; }catch(e){} return W*(.62+Math.random()*.22); })(),sp);")

# big moves: sooner and more often, the ones Hector named
js = once(js, "var nextAnim=20+Math.random()*25,", "var nextAnim=9+Math.random()*8,")
js = once(js, "nextAnim=t+30+Math.random()*30;", "nextAnim=t+24+Math.random()*20;")
js = once(js, "var ANIMS=['crate','crate','storm','drone','drone','probe','swarm','flyover','workout','workout'];",
              "var ANIMS=['drone','drone','probe','swarm','flyover','workout','workout','crate'];")

# between big moves: he stays put; now and then he crosses to another part of the page
js = once_re(js, r"      if\(r<\.2\)\{ var nx=Math\.max.*?\n      else startAct\('look'\);\n",
    "      if(r<.12){ var nx=V.x,tries=0; while(Math.abs(nx-V.x)<W*.22&&tries++<8) nx=8*S+Math.random()*Math.max(1,W-56*S);\n"
    "        try{ if(window.PET_PICK){ var pk=window.PET_PICK(W,S,V.x); if(isFinite(pk)) nx=pk; } }catch(e){}   // WEB: the page says where he can be seen\n"
    "        V.dir=nx>V.x?1:-1; walk(V,nx,sp*(.7+Math.random()*.3)); mode='walk'; }   // WEB: off to another part of the page\n"
    "      else if(r<.46){ mode='idle'; timer=6+Math.random()*6; }             // WEB: once there, he stays\n"
    "      else if(r<.70){ if(opts.bubbles) chat(); mode='idle'; timer=5+Math.random()*3; }\n"
    "      else if(r<.80) startAct('wave');\n"
    "      else if(r<.89) startAct('flourish');\n"
    "      else if(r<.97) startAct('throw');\n"
    "      else startAct('look');\n")

# lines for the web door
js = once_re(js, r"    idle:\[[^\]]*\],\n",
    "    idle:['Ask him something.','Esquiffis is listening.','*mechanical breathing*','The web door is open.',\n"
    "          'Check the smoker, pitmaster.','Hydrate, apprentice.','Same Esquiffis. Same Empire.','Your inbox fears you.',\n"
    "          'I find your lack of questions disturbing.','Join the dark side. We have coffee.','I am watching this page.'],\n"
    "    greet:['Welcome back, Hector.','The web door. I approve.','Same Esquiffis as your phone.'],\n"
    "    thinking:['He is looking. Patience.','Esquiffis is on it.','Checking. Stand by.','Give him a moment.'],\n"
    "    waiting:['Still on it.','A big one. He is still working.','Patience, apprentice.'],\n"
    "    reply:['There. Answered.','Esquiffis delivers.','Read it, apprentice.'],\n"
    "    guard:['The guard caught that one.','He almost made that up. Blocked.'],\n"
    "    failed:['The line went dead. Ask again.','No answer. Try once more.'],\n"
    "    locked:['Access denied.','Wrong code, rebel.'],\n")
js = once(js, "    celebrate:['Task complete. Impressive.','The Force is strong with this code.','Another one for the Empire.'],",
              "    celebrate:['Answered. Impressive.','Esquiffis delivers.','Another one for the Empire.'],")

# the page's hook
js = once(js, "  window.pet={\n",
    "  window.pet={\n"
    "    // WEB: the page makes him react. A reply gets the victory twirl (at most every 20 s), the rest a line.\n"
    "    react:function(kind){\n"
    "      if(paused||sceneKey!=='roam'||!roam) return;\n"
    "      var now=performance.now();\n"
    "      if(kind==='reply'&&now-lastCelebrate>20000&&roam.act('celebrate')) lastCelebrate=now;\n"
    "      else say(kind,null,kind==='thinking'?5:3.4);\n"
    "      wake();\n"
    "    },\n")

# start the loop on a timer
js = once(js, "running=true; last=lastDraw=performance.now(); requestAnimationFrame(frame);",
              "running=true; last=lastDraw=performance.now(); if(opts.sched==='timer') setTimeout(tick,16); else requestAnimationFrame(frame);")

assert '</script' not in js.lower()
pet = '(function(){\n' if False else ''
page_path = HERE / 'index.html'
page = page_path.read_text()
B, E = '/*VADERCLAWD-BEGIN*/', '/*VADERCLAWD-END*/'
assert page.count(B) == 1 and page.count(E) == 1, 'page markers missing'
out = page[:page.index(B) + len(B)] + '\n' + js + '\n' + page[page.index(E):]
page_path.write_text(out)
print('VaderClawd: %d chars (rig engine %d) -> index.html %d chars' % (len(js), len(engine), len(out)))
