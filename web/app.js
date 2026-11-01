const el=(id)=>document.getElementById(id);
function jsonTransform(minify){try{const value=JSON.parse(el("json").value);el("result").value=minify?JSON.stringify(value):JSON.stringify(value,null,2);el("json-status").textContent="Valid JSON.";el("json-status").style.color="var(--green)";}catch(error){el("result").value="";el("json-status").textContent="Invalid JSON: "+error.message;el("json-status").style.color="#ff9999";}}
el("format").addEventListener("click",()=>jsonTransform(false));el("minify").addEventListener("click",()=>jsonTransform(true));el("clear").addEventListener("click",()=>{el("json").value="";el("result").value="";el("json-status").textContent="Cleared.";});
el("copy").addEventListener("click",async()=>{if(!el("result").value)return;try{await navigator.clipboard.writeText(el("result").value);el("json-status").textContent="Copied."; }catch{el("json-status").textContent="Clipboard unavailable in this browser."; }});
el("run-regex").addEventListener("click",()=>{try{const flags=el("flags").value;const regex=new RegExp(el("pattern").value,flags.includes("g")?flags:flags+"g");const found=[...el("sample").value.matchAll(regex)];el("matches").textContent=found.length?found.map((m,i)=>String(i+1)+". "+JSON.stringify(m[0])+" at index "+m.index).join("\n"):"No matches found.";el("regex-status").textContent=found.length+" match(es).";el("regex-status").style.color="var(--green)";}catch(error){el("matches").textContent="";el("regex-status").textContent="Invalid regex: "+error.message;el("regex-status").style.color="#ff9999";}});
function transformUrl(encode) {
  const value = el("url-input").value;
  const mode = el("url-mode").value;
  const transform = mode === "uri"
    ? (encode ? encodeURI : decodeURI)
    : (encode ? encodeURIComponent : decodeURIComponent);
  try {
    el("url-output").value = transform(value);
    el("url-status").textContent = encode ? "Encoded successfully." : "Decoded successfully.";
    el("url-status").style.color = "var(--green)";
  } catch (error) {
    el("url-output").value = "";
    el("url-status").textContent = "Could not decode input: " + error.message;
    el("url-status").style.color = "#ff9999";
  }
}
el("url-encode").addEventListener("click", () => transformUrl(true));
el("url-decode").addEventListener("click", () => transformUrl(false));
el("url-clear").addEventListener("click", () => {
  el("url-input").value = "";
  el("url-output").value = "";
  el("url-status").textContent = "Cleared.";
  el("url-status").style.color = "var(--muted)";
});
el("url-copy").addEventListener("click", async () => {
  if (!el("url-output").value) return;
  try {
    await navigator.clipboard.writeText(el("url-output").value);
    el("url-status").textContent = "Copied.";
  } catch {
    el("url-status").textContent = "Clipboard unavailable in this browser.";
  }
});
