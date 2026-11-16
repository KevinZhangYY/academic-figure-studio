const button=document.getElementById('checkUpdates'),dialog=document.getElementById('updateDialog');
const text=document.getElementById('updateMessage'),download=document.getElementById('updateDownload'),releases=document.getElementById('updateRelease');
document.getElementById('closeUpdate').onclick=()=>dialog.close();
async function check(manual=false){
 button.disabled=true;
 try{
  const response=await fetch('/api/update');if(!response.ok)throw Error('检查失败');
  const info=await response.json();
  text.textContent=info.error||(info.available?`发现新版本 ${info.latestVersion}，当前为 ${info.currentVersion}。请先保存项目，下载新 EXE 后退出旧版，再启动新版。`:`当前版本 ${info.currentVersion}，暂未发现更新的 Windows 安装包。`);
  download.hidden=!info.available;
  // Backend only returns the fixed repository's HTTPS release URLs.
  if(info.available)download.href=info.downloadUrl;
  releases.href=info.releaseUrl;
  if(manual||info.available){if(!dialog.open)dialog.showModal()}
 }catch{
  if(manual){text.textContent='暂时无法检查更新，请确认网络连接后重试。';download.hidden=true;if(!dialog.open)dialog.showModal()}
 }finally{button.disabled=false}
}
button.onclick=()=>check(true);
fetch('/api/health').then(r=>r.json()).then(info=>{button.title=`当前版本 ${info.version}`;if(info.desktop)check()}).catch(()=>{});
