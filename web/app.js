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


// Heuristic Docker Compose checks. YAML is parsed locally with js-yaml.
function checkComposeConfig(config){
  const findings=[];
  const add=(level,path,message)=>findings.push({level,path,message});
  if(!config||typeof config!=="object"||Array.isArray(config)){
    add("ERROR","<root>","The Compose document must be a YAML mapping.");
    return findings;
  }
  if(!config.services||typeof config.services!=="object"||Array.isArray(config.services)){
    add("ERROR","services","A top-level services mapping is required.");
    return findings;
  }
  const services=Object.entries(config.services);
  if(!services.length)add("ERROR","services","Define at least one service.");
  for(const [name,service] of services){
    const base="services."+name;
    if(!service||typeof service!=="object"||Array.isArray(service)){
      add("ERROR",base,"Each service must be a mapping.");
      continue;
    }
    if(!service.image&&!service.build)add("ERROR",base,"Set either image or build for this service.");
    if(service.image&&typeof service.image!=="string")add("ERROR",base+".image","Image must be a string.");
    if(service.build&&typeof service.build!=="string"&&(typeof service.build!=="object"||Array.isArray(service.build)))add("ERROR",base+".build","Build must be a path or mapping.");
    if(service.ports!==undefined&&!Array.isArray(service.ports))add("ERROR",base+".ports","Ports must be a list.");
    if(Array.isArray(service.ports))service.ports.forEach((port,index)=>{
      if(typeof port!=="string"&&(!port||typeof port!=="object"))add("ERROR",base+".ports["+index+"]","Each port entry must be a string or mapping.");
    });
    if(service.volumes!==undefined&&!Array.isArray(service.volumes))add("ERROR",base+".volumes","Volumes must be a list.");
    if(Array.isArray(service.volumes))service.volumes.forEach((volume,index)=>{
      if(typeof volume!=="string"&&(!volume||typeof volume!=="object"))add("ERROR",base+".volumes["+index+"]","Each volume entry must be a string or mapping.");
    });
    if(service.environment!==undefined&&!Array.isArray(service.environment)&&(typeof service.environment!=="object"||service.environment===null))add("ERROR",base+".environment","Environment must be a list or mapping.");
    if(service.depends_on!==undefined&&!Array.isArray(service.depends_on)&&(typeof service.depends_on!=="object"||service.depends_on===null))add("ERROR",base+".depends_on","depends_on must be a list or mapping.");
    if(service.privileged===true)add("WARN",base+".privileged","Privileged mode grants broad host access. Avoid it unless essential.");
    if(service.network_mode==="host")add("WARN",base+".network_mode","Host networking reduces network isolation.");
    if(service.restart==="always")add("INFO",base+".restart","Consider whether always is appropriate for this service's lifecycle.");
    if(service.container_name)add("INFO",base+".container_name","Fixed container names can prevent scaling this service.");
  }
  for(const key of ["volumes","networks","configs","secrets"]){
    if(config[key]!==undefined&&(typeof config[key]!=="object"||config[key]===null||Array.isArray(config[key])))add("ERROR",key,"Top-level "+key+" must be a mapping.");
  }
  if(config.version!==undefined)add("INFO","version","The top-level version field is obsolete in the current Compose Specification and can usually be removed.");
  if(!findings.length)add("PASS","<root>","No common structural issues found.");
  return findings;
}
function renderComposeFindings(findings){
  const output=el("compose-findings");output.replaceChildren();
  const counts={ERROR:0,WARN:0,INFO:0,PASS:0};
  for(const finding of findings){
    counts[finding.level]++;
    const row=document.createElement("div");row.className="diff-line "+(finding.level==="ERROR"?"removed":finding.level==="WARN"?"added":"same");
    const marker=document.createElement("span");marker.className="diff-marker";marker.textContent=finding.level;
    const content=document.createElement("span");content.className="diff-content";content.textContent=finding.path+" — "+finding.message;
    row.append(marker,content);output.append(row);
  }
  el("compose-summary").textContent=counts.ERROR+" errors · "+counts.WARN+" warnings · "+counts.INFO+" info · "+counts.PASS+" pass";
}
el("check-compose").addEventListener("click",()=>{
  try{
    if(!window.jsyaml)throw new Error("The YAML parser could not load. Check your internet connection and refresh.");
    const config=window.jsyaml.load(el("compose-input").value,{schema:window.jsyaml.DEFAULT_SCHEMA});
    const findings=checkComposeConfig(config);
    renderComposeFindings(findings);
    const errors=findings.filter(item=>item.level==="ERROR").length;
    el("compose-status").textContent=errors?"Checks completed with "+errors+" error(s).":"Checks completed. Review warnings and info before running Compose.";
    el("compose-status").style.color=errors?"#ff9999":"var(--green)";
  }catch(error){
    renderComposeFindings([{level:"ERROR",path:"YAML",message:error.message}]);
    el("compose-status").textContent="Could not check this file.";
    el("compose-status").style.color="#ff9999";
  }
});
el("clear-compose").addEventListener("click",()=>{
  el("compose-input").value="";el("compose-findings").replaceChildren();el("compose-summary").textContent="";
  el("compose-status").textContent="Cleared.";el("compose-status").style.color="var(--muted)";
});


// GitHub Actions workflow review: heuristic checks over parsed YAML.
function inspectWorkflow(workflow){
  const findings=[];
  const add=(level,path,message)=>findings.push({level,path,message});
  if(!workflow||typeof workflow!=="object"||Array.isArray(workflow)){
    add("ERROR","<root>","The workflow document must be a YAML mapping.");
    return findings;
  }
  const triggers=workflow.on??workflow.true;
  if(triggers===undefined)add("ERROR","on","No workflow trigger was found. Add push, pull_request, workflow_dispatch, or another event.");
  else if(Array.isArray(triggers)&&triggers.length===0)add("WARN","on","The workflow trigger list is empty.");
  if(!workflow.jobs||typeof workflow.jobs!=="object"||Array.isArray(workflow.jobs)){
    add("ERROR","jobs","A top-level jobs mapping is required.");
    return findings;
  }
  const jobs=Object.entries(workflow.jobs);
  if(!jobs.length)add("ERROR","jobs","Define at least one job.");
  const globalPermissions=workflow.permissions;
  const hasGlobalPermissions=globalPermissions!==undefined;
  if(globalPermissions==="write-all")add("ERROR","permissions","write-all grants broad token permissions. Use explicit least-privilege permissions.");
  else if(globalPermissions==="read-all")add("INFO","permissions","read-all is broad; consider declaring only the scopes the workflow needs.");
  for(const [jobName,job] of jobs){
    const base="jobs."+jobName;
    if(!job||typeof job!=="object"||Array.isArray(job)){
      add("ERROR",base,"Each job must be a mapping.");
      continue;
    }
    if(!job["runs-on"]&&!job.uses)add("ERROR",base,"A job needs runs-on or a reusable-workflow uses reference.");
    if(!job.steps&&!job.uses)add("ERROR",base+".steps","A regular job must define a steps list.");
    if(Array.isArray(job.steps)&&job.steps.length===0)add("WARN",base+".steps","This job has no steps.");
    if(typeof job.uses==="string"&&!job.uses.startsWith("./")){
      const reusableRef=job.uses.slice(job.uses.lastIndexOf("@")+1);
      if(!job.uses.includes("@"))add("ERROR",base+".uses","Reusable workflow reference is missing a version or commit SHA.");
      else if(!/^[a-f0-9]{40}$/i.test(reusableRef))add("WARN",base+".uses","Pin reusable workflows to a full 40-character commit SHA where possible.");
    }
    if(job.steps!==undefined&&!Array.isArray(job.steps))add("ERROR",base+".steps","Steps must be a YAML list.");
    if(job["timeout-minutes"]===undefined)add("WARN",base+".timeout-minutes","Set a job timeout-minutes value to prevent stuck jobs from running indefinitely.");
    if(job.permissions==="write-all")add("ERROR",base+".permissions","write-all grants broad token permissions. Use explicit least-privilege permissions.");
    else if(job.permissions===undefined&&!hasGlobalPermissions)add("WARN",base+".permissions","This job inherits default token permissions. Declare the minimum required permissions at workflow or job level.");
    if(job.permissions&&typeof job.permissions==="object"&&!Array.isArray(job.permissions)){
      for(const [scope,permission] of Object.entries(job.permissions)){
        if(permission==="write-all")add("ERROR",base+".permissions."+scope,"Avoid write-all permissions.");
      }
    }
    if(Array.isArray(job.steps)){
      job.steps.forEach((step,index)=>{
        const stepPath=base+".steps["+index+"]";
        if(!step||typeof step!=="object"||Array.isArray(step)){
          add("ERROR",stepPath,"Each step must be a mapping.");
          return;
        }
        if(!step.uses&&!step.run)add("ERROR",stepPath,"A step needs either uses or run.");
        if(step.uses&&step.run)add("WARN",stepPath,"A step normally uses either uses or run, not both.");
        if(typeof step.uses==="string"){
          const uses=step.uses;
          if(uses.startsWith("./")||uses.startsWith("docker://")) {
            // Local and Docker actions do not use the same remote SHA pinning convention.
          } else if(uses.includes("@")){
            const ref=uses.slice(uses.lastIndexOf("@")+1);
            if(!/^[a-f0-9]{40}$/i.test(ref))add("WARN",stepPath+".uses","Pin third-party actions to a full 40-character commit SHA; a version tag can move.");
          } else add("ERROR",stepPath+".uses","Action reference is missing a version or commit SHA.");
        }
        const runText=typeof step.run==="string"?step.run:"";
        const untrustedContexts=["github.event.pull_request.title","github.event.pull_request.body","github.event.pull_request.head.ref","github.event.issue.title","github.event.issue.body","github.event.comment.body"];
        for(const context of untrustedContexts){
          if(runText.includes("${{ "+context+" }}")||runText.includes("${{"+context+"}}")){
            add("ERROR",stepPath+".run","Potential script injection: untrusted event data is interpolated directly into a run command. Pass it through an environment variable and validate it.");
            break;
          }
        }
      });
    }
  }
  const eventNames=Array.isArray(triggers)?triggers:typeof triggers==="string"?[triggers]:Object.keys(triggers&&typeof triggers==="object"?triggers:{});
  if(eventNames.includes("pull_request_target")){
    add("WARN","on.pull_request_target","This event runs with elevated trust for pull requests from forks. Avoid checking out or executing untrusted pull-request code.");
    for(const [jobName,job] of jobs){
      if(!Array.isArray(job?.steps))continue;
      job.steps.forEach((step,index)=>{
        if(typeof step?.uses==="string"&&step.uses.startsWith("actions/checkout")&&String(step.with?.ref||"").includes("github.event.pull_request.head")){
          add("ERROR","jobs."+jobName+".steps["+index+"].with.ref","This checks out pull-request head code in a pull_request_target workflow. Do not execute untrusted fork code in this privileged context.");
        }
      });
    }
  }
  if(!findings.length)add("PASS","<root>","No common workflow issues found by these checks.");
  return findings;
}
function renderWorkflowFindings(findings){
  const output=el("workflow-findings");output.replaceChildren();
  const counts={ERROR:0,WARN:0,INFO:0,PASS:0};
  for(const finding of findings){
    counts[finding.level]++;
    const row=document.createElement("div");
    row.className="diff-line "+(finding.level==="ERROR"?"removed":finding.level==="WARN"?"added":"same");
    const marker=document.createElement("span");marker.className="diff-marker";marker.textContent=finding.level;
    const content=document.createElement("span");content.className="diff-content";content.textContent=finding.path+" — "+finding.message;
    row.append(marker,content);output.append(row);
  }
  el("workflow-summary").textContent=counts.ERROR+" errors · "+counts.WARN+" warnings · "+counts.INFO+" info · "+counts.PASS+" pass";
}
let latestWorkflowReport="";
el("check-workflow").addEventListener("click",()=>{
  try{
    if(!window.jsyaml)throw new Error("The YAML parser could not load. Check your internet connection and refresh.");
    const workflow=window.jsyaml.load(el("workflow-input").value,{schema:window.jsyaml.DEFAULT_SCHEMA});
    const findings=inspectWorkflow(workflow);
    renderWorkflowFindings(findings);
    latestWorkflowReport=findings.map(item=>"["+item.level+"] "+item.path+" — "+item.message).join("\n");
    const errors=findings.filter(item=>item.level==="ERROR").length;
    el("workflow-status").textContent="Analysis complete. "+errors+" error(s) found.";
    el("workflow-status").style.color=errors?"#ff9999":"var(--green)";
  }catch(error){
    const findings=[{level:"ERROR",path:"YAML",message:error.message}];
    renderWorkflowFindings(findings);
    latestWorkflowReport="[ERROR] YAML — "+error.message;
    el("workflow-status").textContent="Could not analyze this workflow.";
    el("workflow-status").style.color="#ff9999";
  }
});
el("clear-workflow").addEventListener("click",()=>{
  el("workflow-input").value="";el("workflow-findings").replaceChildren();el("workflow-summary").textContent="";
  el("workflow-status").textContent="Cleared.";el("workflow-status").style.color="var(--muted)";latestWorkflowReport="";
});
el("copy-workflow-report").addEventListener("click",async()=>{
  if(!latestWorkflowReport)return;
  try{await navigator.clipboard.writeText(latestWorkflowReport);el("workflow-status").textContent="Workflow report copied.";}
  catch{el("workflow-status").textContent="Clipboard unavailable in this browser.";}
});


// Public GitHub repository health scan. Read-only; no token or backend.
let latestRepositoryReport="";
let lastRepositoryFindings=[];
function repositoryFinding(level,path,message){
  return {level,path,message};
}
async function githubGet(url){
  const response=await fetch(url,{headers:{
    Accept:"application/vnd.github+json",
    "X-GitHub-Api-Version":"2022-11-28"
  }});
  if(!response.ok){
    const error=new Error("GitHub API returned HTTP "+response.status+" for "+url.split("/repos/").pop());
    error.status=response.status;
    throw error;
  }
  return response.json();
}
function parseRepositoryUrl(value){
  let parsed;
  try{parsed=new URL(value.trim());}catch{throw new Error("Enter a valid GitHub repository URL.");}
  if(parsed.hostname!=="github.com")throw new Error("Only github.com repository URLs are supported.");
  const parts=parsed.pathname.split("/").filter(Boolean);
  if(parts.length!==2)throw new Error("Use a repository URL in the form https://github.com/owner/repository.");
  const owner=parts[0],name=parts[1].replace(/\.git$/i,"");
  if(!/^[A-Za-z0-9-]+$/.test(owner)||!/^[-_.A-Za-z0-9]+$/.test(name))throw new Error("The repository URL contains an invalid owner or repository name.");
  return {owner,name,fullName:owner+"/"+name};
}
async function inspectPublicRepository(owner,name){
  const base="https://api.github.com/repos/"+encodeURIComponent(owner)+"/"+encodeURIComponent(name);
  const metadata=await githubGet(base);
  const findings=[];
  const add=(level,path,message)=>findings.push(repositoryFinding(level,path,message));
  if(metadata.private)add("INFO","visibility","This repository is private. Public-file checks may be limited.");
  else add("PASS","visibility","Repository is publicly accessible.");
  if(metadata.description)add("PASS","description","Repository has a description.");
  else add("WARN","description","Add a short repository description so visitors can quickly understand its purpose.");
  if(metadata.license?.spdx_id&&metadata.license.spdx_id!=="NOASSERTION")add("PASS","license","License detected: "+metadata.license.spdx_id+".");
  else add("WARN","license","No recognized repository license was detected. Add a LICENSE file to clarify reuse permissions.");
  if(metadata.has_issues)add("PASS","issues","GitHub Issues are enabled.");
  else add("INFO","issues","GitHub Issues are disabled.");
  if(metadata.archived)add("WARN","archived","This repository is archived and read-only.");
  if(metadata.default_branch)add("PASS","default_branch","Default branch: "+metadata.default_branch+".");
  if(Array.isArray(metadata.topics)&&metadata.topics.length)add("PASS","topics","Repository topics are configured ("+metadata.topics.length+").");
  else add("INFO","topics","Consider adding repository topics to improve discoverability.");
  const checks=[
    {label:"README",paths:["README.md"],description:"A README explains the project's purpose and how to get started."},
    {label:"CONTRIBUTING",paths:["CONTRIBUTING.md",".github/CONTRIBUTING.md","docs/CONTRIBUTING.md"],description:"Contribution guidance helps new contributors make useful changes."},
    {label:"CODE_OF_CONDUCT",paths:["CODE_OF_CONDUCT.md",".github/CODE_OF_CONDUCT.md"],description:"A code of conduct sets expectations for community participation."},
    {label:"SECURITY",paths:["SECURITY.md",".github/SECURITY.md"],description:"A security policy explains how to report vulnerabilities responsibly."}
  ];
  const results=await Promise.all(checks.map(async({label,paths,description})=>{
    for(const path of paths){
      try{
        await githubGet(base+"/contents/"+path);
        return {path,label,description,exists:true};
      }catch(error){
        if(error.status!==404)throw error;
      }
    }
    return {path:paths[0],label,description,exists:false};
  }));
  for(const item of results){
    if(item.exists)add("PASS",item.path,item.label+" file found.");
    else add(item.label==="README"||item.label==="SECURITY"?"WARN":"INFO",item.path,"No "+item.label+".md file found in the recognized locations. "+item.description);
  }
  const directoryChecks=[
    [".github/ISSUE_TEMPLATE","issue_templates","Issue templates make bug reports and feature requests easier to submit."],
    [".github/workflows","workflows","GitHub Actions workflows provide automated checks."]
  ];
  const directories=await Promise.all(directoryChecks.map(async([path,key,description])=>{
    try{
      const value=await githubGet(base+"/contents/"+path);
      const count=Array.isArray(value)?value.filter(item=>item.type==="file"&&item.name.endsWith(".yml")||item.type==="file"&&item.name.endsWith(".yaml")).length:0;
      return {path,key,description,exists:Array.isArray(value)&&value.length>0,count};
    }catch(error){if(error.status===404)return {path,key,description,exists:false,count:0};throw error;}
  }));
  for(const item of directories){
    if(item.exists)add("PASS",item.path,item.key==="workflows"?"Workflow directory found ("+item.count+" YAML workflow file(s)).":"Issue template directory found.");
    else add("INFO",item.path,"No "+item.key.replace("_"," ")+" were detected. "+item.description);
  }
  add("INFO","branch_protection","Branch protection cannot be reliably inspected through the unauthenticated public API. Check repository Settings → Rules separately.");
  add("INFO","security_settings","Private security settings (such as secret scanning and Dependabot alert configuration) are not exposed by this public scan.");
  if(metadata.fork)add("INFO","fork","This repository is a fork; review whether upstream changes should be synchronized.");
  return {metadata,findings};
}
function renderRepositoryFindings(findings){
  const output=el("repository-findings");output.replaceChildren();
  const counts={ERROR:0,WARN:0,INFO:0,PASS:0};
  for(const finding of findings){
    counts[finding.level]++;
    const row=document.createElement("div");
    row.className="diff-line "+(finding.level==="ERROR"||finding.level==="WARN"?"removed":finding.level==="PASS"?"same":"added");
    const marker=document.createElement("span");marker.className="diff-marker";marker.textContent=finding.level;
    const content=document.createElement("span");content.className="diff-content";content.textContent=finding.path+" — "+finding.message;
    row.append(marker,content);output.append(row);
  }
  el("repository-summary").textContent=counts.ERROR+" errors · "+counts.WARN+" warnings · "+counts.INFO+" info · "+counts.PASS+" pass";
}
el("scan-repository").addEventListener("click",async()=>{
  const button=el("scan-repository");
  button.disabled=true;el("repository-status").textContent="Scanning public repository metadata and files…";
  el("repository-status").style.color="var(--muted)";
  el("repository-findings").replaceChildren();el("repository-summary").textContent="";latestRepositoryReport="";
  try{
    const target=parseRepositoryUrl(el("repo-url").value);
    const result=await inspectPublicRepository(target.owner,target.name);
    lastRepositoryFindings=result.findings;
    renderRepositoryFindings(result.findings);
    latestRepositoryReport="# Repository health report: "+target.fullName+"\n\n"+
      result.findings.map(item=>"["+item.level+"] "+item.path+" — "+item.message).join("\n");
    const warnings=result.findings.filter(item=>item.level==="WARN").length;
    el("repository-status").textContent="Scan complete for "+target.fullName+". "+warnings+" warning(s) found.";
    el("repository-status").style.color=warnings?"#ff9999":"var(--green)";
  }catch(error){
    const message=error.status===403?"GitHub API rate limit or access restriction. Try again later.":error.status===404?"Repository not found or not publicly accessible.":error.message;
    const findings=[repositoryFinding("ERROR","scan",message)];
    renderRepositoryFindings(findings);latestRepositoryReport="[ERROR] scan — "+message;
    el("repository-status").textContent="Repository scan could not be completed.";
    el("repository-status").style.color="#ff9999";
  }finally{button.disabled=false;}
});
el("clear-repository").addEventListener("click",()=>{
  el("repo-url").value="";el("repository-findings").replaceChildren();el("repository-summary").textContent="";
  el("repository-status").textContent="Enter a public GitHub repository URL to begin.";
  el("repository-status").style.color="var(--muted)";latestRepositoryReport="";
});
el("copy-repository-report").addEventListener("click",async()=>{
  if(!latestRepositoryReport)return;
  try{await navigator.clipboard.writeText(latestRepositoryReport);el("repository-status").textContent="Repository report copied.";}
  catch{el("repository-status").textContent="Clipboard unavailable in this browser.";}
});


// Repository topics suggestions: curated keyword matching, no network calls.
let latestTopics=[];
el("analyze-topics").addEventListener("click",()=>{
  const source=[el("topics-name").value,el("topics-description").value,el("topics-stack").value].join(" ").toLowerCase();
  const rules=[
    ["python",/python|typer|django|flask|fastapi/],["javascript",/javascript|\bjs\b|node|npm/],
    ["typescript",/typescript|\bts\b/],["cli",/command.line|\bcli\b|terminal/],
    ["developer-tools",/developer|dev tools|toolkit|debug/],["open-source",/open.source|community|contribut/],
    ["privacy",/privacy|local.first|offline|on.device/],["security",/security|vulnerabilit|secret|audit/],
    ["automation",/automation|workflow|ci\/cd|pipeline/],["testing",/test|pytest|jest|vitest/],
    ["docker",/docker|container|compose/],["github-actions",/github actions|workflow|actions/],
    ["documentation",/readme|documentation|docs|markdown/],["api",/\bapi\b|http|rest/],
    ["web",/website|web app|browser|frontend/],["react",/react|vite/],
    ["rust",/rust|cargo/],["go",/golang|\bgo\b/],["java",/java|gradle|maven/]
  ];
  const matches=rules.filter(([,pattern])=>pattern.test(source)).map(([topic])=>topic);
  if(!matches.length)matches.push("developer-tools","open-source");
  latestTopics=[...new Set(matches)].slice(0,20);
  const out=el("topics-results");out.replaceChildren();
  latestTopics.forEach(topic=>{const row=document.createElement("div");row.className="diff-line same";row.textContent=topic;out.append(row);});
  el("topics-status").textContent=latestTopics.length+" topic suggestions. Review them before adding to GitHub.";
});
el("copy-topics").addEventListener("click",async()=>{
  if(!latestTopics.length)return;
  try{await navigator.clipboard.writeText(latestTopics.join(", "));el("topics-status").textContent="Topics copied.";}
  catch{el("topics-status").textContent="Clipboard unavailable in this browser.";}
});

// Transparent checklist score based on the most recent repository scan.
el("score-repository").addEventListener("click",()=>{
  if(!lastRepositoryFindings.length){el("score-status").textContent="Run the Repository Health Checker first.";return;}
  const pass=lastRepositoryFindings.filter(x=>x.level==="PASS").length;
  const warn=lastRepositoryFindings.filter(x=>x.level==="WARN").length;
  const errors=lastRepositoryFindings.filter(x=>x.level==="ERROR").length;
  const total=pass+warn+errors;
  const score=total?Math.round((pass/total)*100):0;
  el("score-summary").textContent="Checklist score: "+score+"/100 · "+pass+" pass · "+warn+" warnings · "+errors+" errors";
  const output=el("score-findings");output.replaceChildren();
  const note=document.createElement("p");note.textContent="Informational checks are excluded. This score measures only the presence of checklist items and is not a security assessment.";output.append(note);
  lastRepositoryFindings.filter(x=>x.level!=="INFO").forEach(item=>{
    const row=document.createElement("div");row.className="diff-line "+(item.level==="PASS"?"same":"removed");
    row.textContent="["+item.level+"] "+item.path+" — "+item.message;output.append(row);
  });
  el("score-status").textContent="Score calculated from the latest public repository scan.";
});

// README completeness checks use headings and text only.
el("analyze-readme").addEventListener("click",()=>{
  const source=el("readme-input").value;
  if(!source.trim()){el("readme-status").textContent="Paste README Markdown first.";return;}
  const lower=source.toLowerCase();
  const checks=[
    ["Project title",/^#\s+\S/m.test(source)],
    ["Project description",source.trim().split(/\n+/).some(line=>line.trim()&&!line.trim().startsWith("#")&&line.trim().length>20)],
    ["Installation / getting started",/installation|getting started|quick start|setup/.test(lower)],
    ["Usage / examples",/usage|example|quick start|how to use/.test(lower)],
    ["Features",/features|what it does/.test(lower)],
    ["License",/license/.test(lower)],
    ["Contributing guidance",/contribut/.test(lower)],
    ["Support / issue reporting",/support|issues|bug report/.test(lower)],
    ["Screenshots / demo",/screenshot|demo|preview/.test(lower)],
    ["Badges",/!\[[^\]]*\]\(https?:\/\/|shields\.io/.test(source)]
  ];
  const output=el("readme-findings");output.replaceChildren();
  checks.forEach(([label,ok])=>{const row=document.createElement("div");row.className="diff-line "+(ok?"same":"added");row.textContent=(ok?"PASS  ":"REVIEW  ")+label;output.append(row);});
  const pass=checks.filter(x=>x[1]).length;
  el("readme-summary").textContent=pass+"/"+checks.length+" README checklist items present.";
  el("readme-status").textContent="Static review complete. Recommendations are guidance, not a quality grade.";
});
el("clear-readme").addEventListener("click",()=>{el("readme-input").value="";el("readme-findings").replaceChildren();el("readme-summary").textContent="";el("readme-status").textContent="Cleared.";});

// Common Git commands are described without running or changing repository state.
const gitHelp=[
  {test:/^git status(?:\s|$)/,text:"Shows the current branch and working-tree state: modified, staged, and untracked files. It does not change files."},
  {test:/^git add(?:\s|$)/,text:"Stages selected changes for the next commit. Review the staged diff before committing."},
  {test:/^git commit(?:\s|$)/,text:"Creates a commit from staged changes. The commit records a snapshot and message."},
  {test:/^git push(?:\s|$)/,text:"Uploads local commits to a remote repository. Check the destination branch before pushing."},
  {test:/^git pull(?:\s|$)/,text:"Fetches remote changes and integrates them into the current branch. It may create a merge or rebase depending on configuration."},
  {test:/^git fetch(?:\s|$)/,text:"Downloads remote references and objects without integrating them into your current branch."},
  {test:/^git clone(?:\s|$)/,text:"Creates a local copy of a remote repository."},
  {test:/^git switch(?:\s|$)/,text:"Changes the current branch. Use -c to create and switch to a new branch."},
  {test:/^git checkout(?:\s|$)/,text:"Switches branches or restores paths, depending on arguments. Older checkout forms can discard uncommitted work."},
  {test:/^git merge(?:\s|$)/,text:"Integrates another branch into the current branch. Resolve conflicts and run tests before pushing."},
  {test:/^git rebase(?:\s|$)/,text:"Replays commits onto a new base to create a more linear history. Avoid rebasing shared published commits unless your team agrees."},
  {test:/^git log(?:\s|$)/,text:"Displays commit history. Add --oneline --graph --decorate for a compact branch view."},
  {test:/^git diff(?:\s|$)/,text:"Shows changes between working-tree, staged, and commit states. Use --staged to inspect what will enter the next commit."},
  {test:/^git restore(?:\s|$)/,text:"Restores file contents. Without --staged it can discard working-tree edits; inspect the path and state first."},
  {test:/^git reset(?:\s|$)/,text:"Moves the current branch reference or unstages changes depending on mode. --hard can discard local work; understand the effect before using it."},
  {test:/^git stash(?:\s|$)/,text:"Temporarily shelves tracked working-tree changes so you can work on something else."},
  {test:/^git cherry-pick(?:\s|$)/,text:"Applies the changes introduced by an existing commit onto the current branch."},
  {test:/^git tag(?:\s|$)/,text:"Lists or creates named references, commonly used to mark release versions."}
];
el("explain-git").addEventListener("click",()=>{
  const command=el("git-command").value.trim().replace(/\s+/g," ");
  const output=el("git-explanation");
  if(!command){el("git-status").textContent="Enter a Git command.";output.textContent="";return;}
  if(!/^git\s/.test(command)){el("git-status").textContent="Enter a command beginning with git.";output.textContent="";return;}
  const match=gitHelp.find(item=>item.test.test(command));
  output.textContent=match?match.text:"This command is not in the built-in guide yet. Use git help <command> or git <command> --help to read the official local manual. DevAid does not execute commands.";
  el("git-status").textContent=match?"Explanation found.":"No built-in explanation available.";
});

// Starter ignore templates. Review project-specific rules before committing.
const ignoreTemplates={
  python:"__pycache__/\n*.py[cod]\n*$py.class\n.Python\n.venv/\nvenv/\nenv/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n.coverage\nhtmlcov/\ndist/\nbuild/\n*.egg-info/\n",
  node:"node_modules/\ndist/\nbuild/\ncoverage/\n.npm/\n*.log\n.env\n.env.*\n!.env.example\n",
  windows:"Thumbs.db\nDesktop.ini\n$RECYCLE.BIN/\n",
  macos:".DS_Store\n.AppleDouble\n.LSOverride\n",
  vscode:".vscode/*\n!.vscode/extensions.json\n!.vscode/settings.json\n",
  jetbrains:".idea/\n*.iml\n",
  java:"*.class\n*.jar\n*.war\n.gradle/\nbuild/\n",
  rust:"/target/\n**/*.rs.bk\n",
  go:"/bin/\n/vendor/\n*.test\n"
};
el("generate-ignore").addEventListener("click",()=>{
  const selected=[...el("ignore-stack").selectedOptions].map(option=>option.value);
  if(!selected.length){el("ignore-status").textContent="Choose at least one preset.";return;}
  const sections=selected.map(key=>"# "+key+"\n"+ignoreTemplates[key]);
  el("ignore-output").value="# Generated by DevAid. Review before committing.\n\n"+sections.join("\n");
  el("ignore-status").textContent="Generated "+selected.length+" preset(s). Review the rules for your project.";
});
el("copy-ignore").addEventListener("click",async()=>{
  if(!el("ignore-output").value)return;
  try{await navigator.clipboard.writeText(el("ignore-output").value);el("ignore-status").textContent=".gitignore copied.";}
  catch{el("ignore-status").textContent="Clipboard unavailable in this browser.";}
});


// Changelog generator: groups pasted commit subjects without invoking Git.
let latestChangelog="";
el("generate-changelog").addEventListener("click",()=>{
  const lines=el("changelog-input").value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  if(!lines.length){el("changelog-status").textContent="Paste at least one commit message.";return;}
  const groups={Features:[],"Bug fixes":[],"Performance":[],Documentation:[],"Maintenance":[]};
  lines.forEach(line=>{
    const match=line.match(/^(feat|fix|perf|docs|refactor|test|build|ci|chore)(?:\([^)]*\))?(!)?:\s*(.+)$/i);
    if(!match){groups.Maintenance.push(line);return;}
    const type=match[1].toLowerCase();
    const title=match[3].replace(/^./,c=>c.toUpperCase())+(match[2]?" (breaking change)":"");
    const bucket=type==="feat"?"Features":type==="fix"?"Bug fixes":type==="perf"?"Performance":type==="docs"?"Documentation":"Maintenance";
    groups[bucket].push(title);
  });
  const heading=el("changelog-version").value.trim()||"Unreleased";
  latestChangelog="# "+heading+"\n";
  Object.entries(groups).forEach(([name,items])=>{if(items.length)latestChangelog+="\n## "+name+"\n"+items.map(x=>"- "+x).join("\n")+"\n";});
  el("changelog-output").value=latestChangelog.trim()+"\n";
  el("changelog-status").textContent=lines.length+" commit message(s) grouped. Review before publishing.";
});
el("copy-changelog").addEventListener("click",async()=>{if(!latestChangelog)return;try{await navigator.clipboard.writeText(latestChangelog);el("changelog-status").textContent="Changelog copied.";}catch{el("changelog-status").textContent="Clipboard unavailable.";}});
// Conventional Commit helper.
let latestCommit="";
el("make-commit").addEventListener("click",()=>{
  const summary=el("commit-summary").value.trim().replace(/\s+/g," ");
  if(!summary){el("commit-status").textContent="Describe the change first.";return;}
  if(summary.length>72){el("commit-status").textContent="Keep the subject under 72 characters; shorten the summary.";return;}
  const type=el("commit-type").value,scope=el("commit-scope").value.trim().replace(/[^a-zA-Z0-9._-]/g,"");
  latestCommit=type+(scope?"("+scope+")":"")+": "+summary.charAt(0).toLowerCase()+summary.slice(1);
  el("commit-output").value=latestCommit;el("commit-status").textContent="Conventional Commit subject generated.";
});
el("copy-commit").addEventListener("click",async()=>{if(!latestCommit)return;try{await navigator.clipboard.writeText(latestCommit);el("commit-status").textContent="Commit message copied.";}catch{el("commit-status").textContent="Clipboard unavailable.";}});
// Safe minimal Markdown renderer: raw HTML is escaped and never inserted as markup.
function escapeMarkdownHtml(value){return value.replace(/[&<>"]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[ch]));}
function renderMarkdown(source){
  const lines=source.replace(/\r/g,"").split("\n"),out=[];let inCode=false,code=[],list=false;
  const inline=value=>value.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>').replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/\*(.+?)\*/g,"<em>$1</em>").replace(/\x60([^\x60]+)\x60/g,"<code>$1</code>");
  const closeList=()=>{if(list){out.push("</ul>");list=false;}};
  for(const line of lines){
    if(line.startsWith("```")){closeList();if(inCode){out.push("<pre><code>"+escapeMarkdownHtml(code.join("\n"))+"</code></pre>");code=[];inCode=false;}else inCode=true;continue;}
    if(inCode){code.push(line);continue;}
    if(!line.trim()){closeList();continue;}
    const heading=line.match(/^(#{1,6})\s+(.+)$/);
    if(heading){closeList();const n=heading[1].length;out.push("<h"+n+">"+inline(escapeMarkdownHtml(heading[2]))+"</h"+n+">");continue;}
    if(/^\s*[-*+]\s+/.test(line)){if(!list){out.push("<ul>");list=true;}out.push("<li>"+inline(escapeMarkdownHtml(line.replace(/^\s*[-*+]\s+/,"")))+"</li>");continue;}
    if(/^>\s?/.test(line)){closeList();out.push("<blockquote>"+inline(escapeMarkdownHtml(line.replace(/^>\s?/,"")))+"</blockquote>");continue;}
    closeList();out.push("<p>"+inline(escapeMarkdownHtml(line))+"</p>");
  }
  closeList();if(inCode)out.push("<pre><code>"+escapeMarkdownHtml(code.join("\n"))+"</code></pre>");
  return out.join("\n");
}
el("markdown-input").addEventListener("input",()=>{el("markdown-preview").innerHTML=renderMarkdown(el("markdown-input").value);});
el("markdown-preview").innerHTML=renderMarkdown(el("markdown-input").value);

// License notes are informational, not a legal compatibility verdict.
const licenseNotes={
  "MIT":"Permissive; generally allows reuse with preservation of copyright and license notices.",
  "Apache-2.0":"Permissive; includes express patent license and NOTICE-related conditions.",
  "BSD-3-Clause":"Permissive; retain notices and follow the non-endorsement condition.",
  "ISC":"Short permissive license, broadly similar in practical effect to MIT.",
  "GPL-2.0-only":"Strong copyleft; distribution of covered combined works can trigger source and same-license obligations.",
  "GPL-3.0-only":"Strong copyleft with additional provisions, including patent-related terms.",
  "LGPL-3.0-only":"Library-focused copyleft; linking and modification details matter.",
  "MPL-2.0":"File-level copyleft; modified MPL-covered files generally remain under MPL when distributed.",
  "AGPL-3.0-only":"Network-use provision can create source-sharing obligations for modified covered software used over a network."
};
el("check-licenses").addEventListener("click",()=>{
  const project=el("project-license").value;
  const deps=[...new Set(el("dependency-licenses").value.split(",").map(x=>x.trim()).filter(Boolean))];
  const out=el("license-results");out.replaceChildren();
  const add=(text)=>{const row=document.createElement("p");row.textContent=text;out.append(row);};
  add("Project license: "+project+". "+(licenseNotes[project]||"No automated compatibility conclusion is provided."));
  if(!deps.length)add("Enter dependency SPDX identifiers to review their license notes.");
  deps.forEach(name=>add(name+": "+(licenseNotes[name]||"Unknown identifier in this guide; verify the exact license and version from the upstream project.")));
  add("Do not infer compatibility from license names alone. Linking, distribution, modifications, exceptions, and jurisdiction can change obligations. Consult the license texts and qualified legal advice for release decisions.");
  el("license-status").textContent="Notes generated for "+deps.length+" dependency license(s); no legal compatibility verdict is made.";
});

// Dependency manifest hygiene scanner; no vulnerability feed is queried.
el("check-dependencies").addEventListener("click",()=>{
  const raw=el("dependency-input").value.trim();if(!raw){el("dependency-status").textContent="Paste a package.json or requirements.txt first.";return;}
  const findings=[];const add=(level,item,message)=>findings.push({level,item,message});
  if(raw.startsWith("{")){
    let data;try{data=JSON.parse(raw);}catch(error){el("dependency-status").textContent="Invalid JSON: "+error.message;return;}
    const groups=["dependencies","devDependencies","optionalDependencies","peerDependencies"];let count=0;
    groups.forEach(group=>Object.entries(data[group]||{}).forEach(([name,version])=>{
      count++;const v=String(version);
      if(v==="*"||v==="latest")add("REVIEW",name,"Unbounded or moving version range ("+v+").");
      else if(/^(git\+|https?:|github:|file:)/i.test(v))add("REVIEW",name,"Non-registry source; verify provenance and pinning.");
      else if(/^[~^><=]/.test(v))add("INFO",name,"Version range allows updates; use a lockfile for reproducible installs.");
    }));
    if(!count)add("INFO","dependencies","No dependency entries found in recognized package.json sections.");
    if(!data.engines||!data.engines.node)add("INFO","engines.node","Node.js version is not declared.");
    add("INFO","lockfile","This pasted manifest cannot establish whether a committed lockfile is present.");
  }else{
    const lines=raw.split(/\r?\n/);let count=0;
    lines.forEach((line,index)=>{
      const value=line.trim();if(!value||value.startsWith("#")||value.startsWith("-r ")||value.startsWith("--"))return;
      count++;
      if(/^(git\+|https?:|file:)/i.test(value))add("REVIEW","line "+(index+1),"Direct URL or VCS dependency; verify source and immutable revision.");
      else if(!/[<>=!~]/.test(value))add("REVIEW",value.split(/[;\s]/)[0],"No version constraint is specified.");
      else if(/===|==/.test(value))add("PASS",value.split(/[<>=!~]/)[0],"Exact version pin found; still verify updates and hashes.");
      else add("INFO",value.split(/[<>=!~]/)[0],"Version constraint found; lockfile and hash practices are not verified.");
    });
    if(!count)add("INFO","requirements","No dependency requirement lines found.");
  }
  const output=el("dependency-findings");output.replaceChildren();
  findings.forEach(item=>{const row=document.createElement("div");row.className="diff-line "+(item.level==="PASS"?"same":item.level==="REVIEW"?"removed":"added");row.textContent="["+item.level+"] "+item.item+" — "+item.message;output.append(row);});
  el("dependency-summary").textContent=findings.length+" manifest hygiene finding(s). No CVE or vulnerability lookup was performed.";
  el("dependency-status").textContent="Static dependency manifest review complete.";
});

// Environment template checks. Never paste real .env values.
el("check-env-template").addEventListener("click",()=>{
  const raw=el("env-template").value;if(!raw.trim()){el("env-status").textContent="Paste a safe .env.example template.";return;}
  const seen=new Set(),findings=[];raw.split(/\r?\n/).forEach((line,index)=>{
    const value=line.trim();if(!value||value.startsWith("#"))return;
    const match=value.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$/);
    if(!match){findings.push("[REVIEW] Line "+(index+1)+" — expected KEY=value syntax.");return;}
    const key=match[1],content=match[2].trim();
    if(seen.has(key))findings.push("[ERROR] "+key+" — duplicate variable.");seen.add(key);
    if(!content)findings.push("[REVIEW] "+key+" — empty example value; add a safe placeholder or explanation.");
    if(/^(changeme|replace.me|your.*here|xxx|todo)$/i.test(content))findings.push("[INFO] "+key+" — placeholder detected; document how to obtain the value.");
    if(/(password|secret|token|api[_-]?key)/i.test(key)&&content&&!/^(changeme|replace.me|your.*here|xxx|todo|<.*>)$/i.test(content))findings.push("[REVIEW] "+key+" — template contains a non-obvious value; ensure it is not a real secret.");
  });
  const out=el("env-findings");out.replaceChildren();
  (findings.length?findings:["[PASS] Template syntax looks consistent."]).forEach(item=>{const row=document.createElement("div");row.className="diff-line "+(item.startsWith("[PASS]")?"same":item.startsWith("[ERROR]")?"removed":"added");row.textContent=item;out.append(row);});
  el("env-status").textContent=findings.length+" template finding(s). This does not inspect your machine environment.";
});

// API response inspector for pasted data only.
el("inspect-api").addEventListener("click",()=>{
  const body=el("api-body").value,code=Number(el("api-status-code").value),type=el("api-content-type").value.toLowerCase();
  const out=el("api-findings");out.replaceChildren();const findings=[];
  if(!Number.isInteger(code)||code<100||code>599){el("api-status").textContent="Enter a valid HTTP status code.";return;}
  findings.push("HTTP "+code+" — "+(code>=200&&code<300?"success response":code>=300&&code<400?"redirect response":code>=400?"client/server error response":"informational response"));
  let parsed,validJson=false;
  if(body.trim()){try{parsed=JSON.parse(body);validJson=true;findings.push("Body: valid JSON; top-level type is "+(Array.isArray(parsed)?"array":parsed===null?"null":typeof parsed)+".");}
    catch(error){findings.push("Body: not valid JSON ("+error.message+").");}}
  else findings.push("Body is empty.");
  if(type.includes("application/json")&&body.trim()&&!validJson)findings.push("Content-Type says JSON but the body could not be parsed as JSON.");
  if(validJson&&Array.isArray(parsed))findings.push("Array contains "+parsed.length+" item(s).");
  if(validJson&&parsed&&typeof parsed==="object"&&!Array.isArray(parsed))findings.push("Top-level keys: "+Object.keys(parsed).slice(0,30).join(", ")+".");
  if(code>=400)findings.push("Inspect the API error contract and request details; do not expose credentials in shared logs.");
  findings.forEach(item=>{const row=document.createElement("div");row.className="diff-line same";row.textContent=item;out.append(row);});
  el("api-summary").textContent="Response inspection complete · "+(validJson?"JSON parsed":"body not parsed as JSON");
  el("api-status").textContent="Pasted response analyzed locally; no request was sent.";
});

// Dockerfile heuristic analyzer.
el("analyze-dockerfile").addEventListener("click",()=>{
  const source=el("dockerfile-input").value;if(!source.trim()){el("dockerfile-status").textContent="Paste a Dockerfile first.";return;}
  const lines=source.split(/\r?\n/),active=lines.map((line,i)=>({line:line.trim(),number:i+1})).filter(x=>x.line&&!x.line.startsWith("#"));
  const instructions=active.map(x=>x.line.split(/\s+/)[0].toUpperCase());
  const findings=[];const add=(level,line,msg)=>findings.push({level,line,msg});
  const from=active.find(x=>/^FROM\s/i.test(x.line));
  if(!from)add("ERROR","—","No FROM instruction found.");
  else if(/:latest\b|^[^:]+$/.test((from.line.split(/\s+/)[1]||"").split(" AS ")[0]))add("REVIEW",from.number,"Base image uses latest or no explicit tag; consider a deliberate version or digest.");
  if(!instructions.includes("USER"))add("REVIEW","—","No USER instruction found; container may run as root.");
  if(!instructions.includes("WORKDIR"))add("INFO","—","No WORKDIR instruction found.");
  if(!instructions.includes("HEALTHCHECK"))add("INFO","—","No HEALTHCHECK instruction found; add one when the service supports meaningful health checks.");
  active.forEach(x=>{
    if(/^ADD\s/i.test(x.line)&&!/^ADD\s+https?:/i.test(x.line))add("INFO",x.number,"Prefer COPY unless archive extraction or remote ADD behavior is needed.");
    if(/^(ARG|ENV)\s+\w*(TOKEN|SECRET|PASSWORD|KEY)\w*=/i.test(x.line))add("ERROR",x.number,"Potential secret in ARG/ENV; inject secrets at runtime instead.");
    if(/^RUN\s/i.test(x.line)&&/apt-get install/.test(x.line)&&!/(rm -rf \/var\/lib\/apt\/lists|--no-install-recommends)/.test(x.line))add("INFO",x.number,"Consider --no-install-recommends and cleaning apt lists in the same layer.");
    if(/^RUN\s/i.test(x.line)&&/pip install/.test(x.line)&&!/--no-cache-dir/.test(x.line))add("INFO",x.number,"Consider pip --no-cache-dir to reduce image layer size.");
  });
  if(!instructions.includes("CMD")&&!instructions.includes("ENTRYPOINT"))add("INFO","—","No CMD or ENTRYPOINT instruction found; confirm intended startup behavior.");
  const out=el("dockerfile-findings");out.replaceChildren();
  findings.forEach(item=>{const row=document.createElement("div");row.className="diff-line "+(item.level==="ERROR"?"removed":item.level==="REVIEW"?"added":"same");row.textContent="["+item.level+"] Line "+item.line+" — "+item.msg;out.append(row);});
  el("dockerfile-summary").textContent=findings.length+" finding(s) · "+findings.filter(x=>x.level==="ERROR").length+" errors · "+findings.filter(x=>x.level==="REVIEW").length+" reviews.";
  el("dockerfile-status").textContent="Static analysis complete; validate with Docker tooling before release.";
});
