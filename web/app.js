const el=(id)=>document.getElementById(id);
function jsonTransform(minify){try{const value=JSON.parse(el("json").value);el("result").value=minify?JSON.stringify(value):JSON.stringify(value,null,2);el("json-status").textContent="Valid JSON.";el("json-status").style.color="var(--green)";}catch(error){el("result").value="";el("json-status").textContent="Invalid JSON: "+error.message;el("json-status").style.color="#ff9999";}}
el("format").addEventListener("click",()=>jsonTransform(false));el("minify").addEventListener("click",()=>jsonTransform(true));el("clear").addEventListener("click",()=>{el("json").value="";el("result").value="";el("json-status").textContent="Cleared.";});
el("copy").addEventListener("click",async()=>{if(!el("result").value)return;try{await navigator.clipboard.writeText(el("result").value);el("json-status").textContent="Copied.";}catch{el("json-status").textContent="Clipboard unavailable in this browser."; }});
el("run-regex").addEventListener("click",()=>{try{const flags=el("flags").value;const regex=new RegExp(el("pattern").value,flags.includes("g")?flags:flags+"g");const found=[...el("sample").value.matchAll(regex)];el("matches").textContent=found.length?found.map((m,i)=>String(i+1)+". "+JSON.stringify(m[0])+" at index "+m.index).join("\n"):"No matches found.";el("regex-status").textContent=found.length+" match(es).";el("regex-status").style.color="var(--green)";}catch(error){el("matches").textContent="";el("regex-status").textContent="Invalid regex: "+error.message;el("regex-status").style.color="#ff9999";}});
function transformUrl(encode) {
  const value=el("url-input").value;const mode=el("url-mode").value;
  const transform=mode==="uri"?(encode?encodeURI:decodeURI):(encode?encodeURIComponent:decodeURIComponent);
  try{el("url-output").value=transform(value);el("url-status").textContent=encode?"Encoded successfully.":"Decoded successfully.";el("url-status").style.color="var(--green)";}
  catch(error){el("url-output").value="";el("url-status").textContent="Could not decode input: "+error.message;el("url-status").style.color="#ff9999";}
}
el("url-encode").addEventListener("click",()=>transformUrl(true));el("url-decode").addEventListener("click",()=>transformUrl(false));
el("url-clear").addEventListener("click",()=>{el("url-input").value="";el("url-output").value="";el("url-status").textContent="Cleared.";el("url-status").style.color="var(--muted)";});
el("url-copy").addEventListener("click",async()=>{if(!el("url-output").value)return;try{await navigator.clipboard.writeText(el("url-output").value);el("url-status").textContent="Copied.";}catch{el("url-status").textContent="Clipboard unavailable in this browser.";}});

// Line-based LCS diff. Inputs are capped to keep memory use predictable in the browser.
function buildLineDiff(beforeText,afterText){
  const before=beforeText.split("\n"),after=afterText.split("\n");
  const cells=(before.length+1)*(after.length+1);
  if(cells>1200000)throw new Error("This comparison is too large for the browser tool. Try smaller snippets.");
  const width=after.length+1,table=new Uint32Array(cells);
  for(let i=before.length-1;i>=0;i--){
    for(let j=after.length-1;j>=0;j--){
      const index=i*width+j;
      table[index]=before[i]===after[j]?table[(i+1)*width+j+1]+1:Math.max(table[(i+1)*width+j],table[i*width+j+1]);
    }
  }
  const rows=[];let i=0,j=0,added=0,removed=0,unchanged=0;
  while(i<before.length&&j<after.length){
    if(before[i]===after[j]){rows.push({type:"same",text:before[i++]});j++;unchanged++;}
    else if(table[(i+1)*width+j]>=table[i*width+j+1]){rows.push({type:"removed",text:before[i++]});removed++;}
    else{rows.push({type:"added",text:after[j++]});added++;}
  }
  while(i<before.length){rows.push({type:"removed",text:before[i++]});removed++;}
  while(j<after.length){rows.push({type:"added",text:after[j++]});added++;}
  return{rows,added,removed,unchanged};
}
let latestDiff="";
function runDiff(){
  try{
    const result=buildLineDiff(el("diff-before").value,el("diff-after").value);
    const output=el("diff-output");output.replaceChildren();latestDiff=result.rows.map(row=>(row.type==="added"?"+ ":row.type==="removed"?"- ":"  ")+row.text).join("\n");
    for(const row of result.rows){
      const line=document.createElement("div");line.className="diff-line "+row.type;
      const marker=document.createElement("span");marker.className="diff-marker";marker.textContent=row.type==="added"?"+":row.type==="removed"?"−":" ";
      const content=document.createElement("span");content.className="diff-content";content.textContent=row.text||" ";
      line.append(marker,content);output.append(line);
    }
    el("diff-summary").textContent=result.added+" added · "+result.removed+" removed · "+result.unchanged+" unchanged";
    el("diff-status").textContent="Comparison complete.";el("diff-status").style.color="var(--green)";
  }catch(error){el("diff-output").replaceChildren();el("diff-summary").textContent="";el("diff-status").textContent=error.message;el("diff-status").style.color="#ff9999";latestDiff="";}
}
el("run-diff").addEventListener("click",runDiff);
el("clear-diff").addEventListener("click",()=>{el("diff-before").value="";el("diff-after").value="";el("diff-output").replaceChildren();el("diff-summary").textContent="";el("diff-status").textContent="Cleared.";el("diff-status").style.color="var(--muted)";latestDiff="";});
el("copy-diff").addEventListener("click",async()=>{if(!latestDiff)return;try{await navigator.clipboard.writeText(latestDiff);el("diff-status").textContent="Diff copied.";}catch{el("diff-status").textContent="Clipboard unavailable in this browser.";}});

// YAML parsing is performed in-browser with the js-yaml parser.
// The parser script is served by jsDelivr; YAML content is never sent to it.
function parseYaml(){
  const source=el("yaml-input").value;
  try{
    if(!window.jsyaml)throw new Error("The YAML parser could not load. Check your internet connection and refresh the page.");
    const value=window.jsyaml.load(source,{schema:window.jsyaml.DEFAULT_SCHEMA});
    el("yaml-output").value=JSON.stringify(value,null,2);
    el("yaml-status").textContent="Valid YAML.";
    el("yaml-status").style.color="var(--green)";
    return value;
  }catch(error){
    el("yaml-output").value="";
    el("yaml-status").textContent="Invalid YAML: "+error.message;
    el("yaml-status").style.color="#ff9999";
    return undefined;
  }
}
el("validate-yaml").addEventListener("click",()=>parseYaml());
el("format-yaml").addEventListener("click",()=>{
  const value=parseYaml();
  if(value===undefined)return;
  el("yaml-input").value=window.jsyaml.dump(value,{noRefs:true,lineWidth:100});
  el("yaml-status").textContent="YAML parsed and formatted.";
});
el("clear-yaml").addEventListener("click",()=>{
  el("yaml-input").value="";el("yaml-output").value="";
  el("yaml-status").textContent="Cleared.";el("yaml-status").style.color="var(--muted)";
});
el("copy-yaml").addEventListener("click",async()=>{
  if(!el("yaml-output").value)return;
  try{await navigator.clipboard.writeText(el("yaml-output").value);el("yaml-status").textContent="Copied parsed JSON.";}
  catch{el("yaml-status").textContent="Clipboard unavailable in this browser.";}
});
