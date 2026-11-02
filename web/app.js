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
