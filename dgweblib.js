function hideObj(objId) {
  var obj;
  obj = document.getElementById(objId);
  obj.style.display = 'none';
}

function showObj(objId) {
  var obj;
  obj = document.getElementById(objId);
  obj.style.display = '';
}

function showhideEngineOptions() {
  var engines = document.getElementsByName('virusengine');
  var i;
  for (i = 0; i < engines.length; i++) {
    if (engines[i].checked) {
      enginevalue = engines[i].value;
    }
  }
  
  if (enginevalue == "clamdscan") {
    showObj('clamdsec');
    hideObj('clamavsec');
    hideObj('aveserversec');
    hideObj('trophiesec');
    hideObj('sophiesec');
    hideObj('icapsec');
  }
  else if (enginevalue == "clamav") {
    hideObj('clamdsec');
    showObj('clamavsec');
    hideObj('aveserversec');
    hideObj('trophiesec');
    hideObj('sophiesec');
    hideObj('icapsec');
  }
  else if (enginevalue == "kav") {
    hideObj('clamdsec');
    hideObj('clamavsec');
    hideObj('aveserversec');
    hideObj('trophiesec');
    hideObj('sophiesec');
    hideObj('icapsec');
  }
  else if (enginevalue == "aveserver") {
    hideObj('clamdsec');
    hideObj('clamavsec');
    showObj('aveserversec');
    hideObj('trophiesec');
    hideObj('sophiesec');
    hideObj('icapsec');
  }
  else if (enginevalue == "trophie") {
    hideObj('clamdsec');
    hideObj('clamavsec');
    hideObj('aveserversec');
    showObj('trophiesec');
    hideObj('sophiesec');
    hideObj('icapsec');
  }
  else if (enginevalue == "sophie") {
    hideObj('clamdsec');
    hideObj('clamavsec');
    hideObj('aveserversec');
    hideObj('trophiesec');
    showObj('sophiesec');
    hideObj('icapsec');
  }
  else if (enginevalue == "icap") {
    hideObj('clamdsec');
    hideObj('clamavsec');
    hideObj('aveserversec');
    hideObj('trophiesec');
    hideObj('sophiesec');
    showObj('icapsec');
  }
}
