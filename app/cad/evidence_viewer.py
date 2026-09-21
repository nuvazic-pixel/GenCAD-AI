
from __future__ import annotations

import base64
import json
from pathlib import Path

from app.cad.feature_language import CADFeatureProgram, FeatureProgramVerificationReport


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:dark;--bg:#090b10;--panel:#11151d;--panel2:#171d28;--line:#252d3b;--text:#ecf1f8;--muted:#9aa6b7;--confirmed:#28c76f;--derived:#f4b942;--hypothesis:#a970ff;--unknown:#ff5d6c;--accent:#5ca9ff}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}
#app{display:grid;grid-template-columns:320px 1fr 360px;height:100vh}
aside{background:var(--panel);overflow:auto}#left{border-right:1px solid var(--line)}#right{border-left:1px solid var(--line)}
header{padding:18px;border-bottom:1px solid var(--line)}h1{margin:0 0 6px;font-size:17px}.sub{color:var(--muted);font-size:12px;line-height:1.45}
.gate{display:inline-flex;margin-top:10px;padding:5px 9px;border-radius:999px;font-size:11px;font-weight:800}.gate.pass{color:var(--confirmed);border:1px solid var(--confirmed)}.gate.fail{color:var(--unknown);border:1px solid var(--unknown)}
#viewport{position:relative;min-width:0}canvas{display:block;width:100%;height:100%}
#hint{position:absolute;left:18px;bottom:16px;background:rgba(9,11,16,.75);padding:8px 11px;border:1px solid var(--line);border-radius:9px;color:var(--muted);font-size:11px}
.section-title{padding:16px 16px 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.11em;font-size:10px;font-weight:800}
.feature{margin:7px 10px;padding:12px;border:1px solid var(--line);border-radius:11px;background:var(--panel2);cursor:pointer}.feature:hover,.feature.active{border-color:var(--accent)}
.row{display:flex;align-items:center;justify-content:space-between;gap:8px}.feature-name{font-weight:700;font-size:13px}.kind{color:var(--muted);font-size:11px;margin-top:5px}
.badge{font-size:9px;font-weight:800;text-transform:uppercase;border-radius:999px;padding:4px 7px}.confirmed{color:var(--confirmed)}.derived{color:var(--derived)}.hypothesis{color:var(--hypothesis)}.unknown{color:var(--unknown)}
#detail{padding:16px}#detail h2{margin:0 0 6px;font-size:18px}.desc{color:var(--muted);font-size:12px;line-height:1.5;margin:10px 0 16px}
.param{padding:11px 0;border-top:1px solid var(--line)}.param-name{font-size:11px;color:var(--muted)}.param-value{font-size:15px;font-weight:750;margin:3px 0 7px}.prov{font-size:10.5px;color:var(--muted);line-height:1.45;word-break:break-word}
.legend{padding:10px 16px 18px;display:grid;grid-template-columns:1fr 1fr;gap:8px}.legend span{font-size:10px;color:var(--muted)}.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.blocked{margin:10px;padding:10px;color:var(--unknown);border:1px solid var(--unknown);border-radius:10px;font-size:11px}
</style>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
</head>
<body>
<div id="app">
<aside id="left"><header><h1>__TITLE__</h1><div class="sub">Evidence-bound CAD feature program<br><span id="program-id"></span></div><div id="gate" class="gate"></div></header><div class="section-title">Features</div><div id="feature-list"></div><div class="section-title">Evidence states</div><div class="legend"><span><i class="dot" style="background:var(--confirmed)"></i>Confirmed</span><span><i class="dot" style="background:var(--derived)"></i>Derived</span><span><i class="dot" style="background:var(--hypothesis)"></i>Hypothesis</span><span><i class="dot" style="background:var(--unknown)"></i>Unknown</span></div><div id="blocked"></div></aside>
<main id="viewport"><div id="hint">Drag to rotate · wheel to zoom · click a feature to inspect evidence</div></main>
<aside id="right"><header><h1>Feature evidence</h1><div class="sub">Every displayed value carries an evidence state.</div></header><div id="detail"></div></aside>
</div>
<script>
var PROGRAM=__PROGRAM__;
var VERIFICATION=__VERIFICATION__;
var STL_B64="__STL_B64__";
var COLORS={confirmed:0x28c76f,derived:0xf4b942,hypothesis:0xa970ff,unknown:0xff5d6c};

function decodeBase64(s){var b=atob(s),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u.buffer}
function featureState(f){var s=Object.keys(f.parameters).map(function(k){return f.parameters[k].state});if(s.indexOf("unknown")>=0)return"unknown";if(s.indexOf("hypothesis")>=0)return"hypothesis";if(s.indexOf("derived")>=0)return"derived";return"confirmed"}

var viewport=document.getElementById("viewport");
var scene=new THREE.Scene();scene.background=new THREE.Color(0x090b10);
var camera=new THREE.PerspectiveCamera(45,1,.1,2000);camera.position.set(95,80,90);
var renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));viewport.insertBefore(renderer.domElement,viewport.firstChild);
var controls=new THREE.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xdde8ff,0x253040,2.2));var key=new THREE.DirectionalLight(0xffffff,3.0);key.position.set(80,100,120);scene.add(key);
var grid=new THREE.GridHelper(160,16,0x313b4b,0x1b2230);grid.rotation.x=Math.PI/2;scene.add(grid);

var loader=new THREE.STLLoader();var geo=loader.parse(decodeBase64(STL_B64));geo.computeVertexNormals();
var finalMesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:0xb9c3d0,metalness:.35,roughness:.58,transparent:true,opacity:.58}));
scene.add(finalMesh);
var bbox=new THREE.Box3().setFromObject(finalMesh);controls.target.copy(bbox.getCenter(new THREE.Vector3()));

function circleShape(inner,outer){var s=new THREE.Shape();s.absarc(0,0,outer,0,Math.PI*2,false);var h=new THREE.Path();h.absarc(0,0,inner,0,Math.PI*2,true);s.holes.push(h);return s}
function overlayFor(f){var p=f.parameters,g=null,m=null;
 if(f.kind==="box"){g=new THREE.BoxGeometry(p.length_mm.value,p.depth_mm.value,p.height_mm.value);m=new THREE.Mesh(g);m.position.z=p.height_mm.value/2}
 else if(f.kind==="annular_extrude"){g=new THREE.ExtrudeGeometry(circleShape(p.inner_radius_mm.value,p.outer_radius_mm.value),{depth:p.depth_mm.value,bevelEnabled:false,curveSegments:64});g.center();g.rotateX(Math.PI/2);m=new THREE.Mesh(g);m.position.z=p.center_z_mm.value}
 else if(f.kind==="cylinder"){var r=(p.diameter_mm.value||2)/2,d=p.depth_mm.value||2;g=new THREE.CylinderGeometry(r,r,d,40);g.rotateX(Math.PI/2);m=new THREE.Mesh(g);m.position.set(p.x_mm.value||0,p.y_mm.value||0,(p.z_start_mm.value||0)+d/2)}
 if(!m)return null;var st=featureState(f);m.material=new THREE.MeshStandardMaterial({color:COLORS[st],transparent:true,opacity:.25,depthWrite:false,wireframe:f.operation==="cut"});m.visible=false;scene.add(m);return m}

var overlays={};PROGRAM.features.forEach(function(f){var o=overlayFor(f);if(o)overlays[f.feature_id]=o});
document.getElementById("program-id").textContent=PROGRAM.program_id;
var gate=document.getElementById("gate");gate.textContent=VERIFICATION.passed?"FEATURE GATE · PASS":"FEATURE GATE · BLOCKED";gate.className="gate "+(VERIFICATION.passed?"pass":"fail");
if(!VERIFICATION.passed){document.getElementById("blocked").innerHTML='<div class="blocked"><b>Blocked parameters</b><br>'+VERIFICATION.blocked_parameters.join("<br>")+"</div>"}

var list=document.getElementById("feature-list"),detail=document.getElementById("detail");
function selectFeature(f){
 document.querySelectorAll(".feature").forEach(function(e){e.classList.remove("active")});var card=document.querySelector('[data-feature="'+f.feature_id+'"]');if(card)card.classList.add("active");
 Object.keys(overlays).forEach(function(id){overlays[id].visible=id===f.feature_id});
 var st=featureState(f),html="<h2>"+f.label+"</h2><span class='badge "+st+"'>"+st+"</span><div class='desc'>"+(f.description||"")+"<br>"+f.operation.toUpperCase()+" · "+f.kind+"</div>";
 Object.keys(f.parameters).forEach(function(name){var p=f.parameters[name],value=p.value===null?"UNKNOWN":String(p.value)+(p.unit?" "+p.unit:""),src=p.source_fields&&p.source_fields.length?p.source_fields.join(", "):"system topology";html+="<div class='param'><div class='param-name'>"+name+"</div><div class='param-value'>"+value+" <span class='badge "+p.state+"'>"+p.state+"</span></div><div class='prov'>Source fields: "+src+(p.rule_id?"<br>Rule: <b>"+p.rule_id+"</b>":"")+(p.note?"<br>Evidence: "+p.note:"")+"</div></div>"});
 detail.innerHTML=html
}
PROGRAM.features.forEach(function(f){var st=featureState(f),card=document.createElement("div");card.className="feature";card.setAttribute("data-feature",f.feature_id);card.innerHTML="<div class='row'><span class='feature-name'>"+f.label+"</span><span class='badge "+st+"'>"+st+"</span></div><div class='kind'>"+f.operation.toUpperCase()+" · "+f.kind+"</div>";card.onclick=function(){selectFeature(f)};list.appendChild(card)});
if(PROGRAM.features.length)selectFeature(PROGRAM.features[0]);

function resize(){var w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}window.addEventListener("resize",resize);resize();
(function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,camera)})();
</script>
</body>
</html>
"""


def build_evidence_viewer_html(
    *,
    program: CADFeatureProgram,
    stl_path: str | Path,
    verification: FeatureProgramVerificationReport,
    title: str = "GenCAD-AI Evidence Viewer",
) -> str:
    html = HTML_TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace(
        "__PROGRAM__",
        json.dumps(program.model_dump(mode="json"), ensure_ascii=False),
    )
    html = html.replace(
        "__VERIFICATION__",
        json.dumps(verification.model_dump(mode="json"), ensure_ascii=False),
    )
    html = html.replace(
        "__STL_B64__",
        base64.b64encode(Path(stl_path).read_bytes()).decode("ascii"),
    )
    return html


def write_evidence_viewer(
    *,
    program: CADFeatureProgram,
    stl_path: str | Path,
    verification: FeatureProgramVerificationReport,
    output_path: str | Path,
    title: str = "GenCAD-AI Evidence Viewer",
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_evidence_viewer_html(
            program=program,
            stl_path=stl_path,
            verification=verification,
            title=title,
        ),
        encoding="utf-8",
    )
    return output
