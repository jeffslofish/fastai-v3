var el = x => document.getElementById(x);

function analyze(e) {
  e.preventDefault();
  el('analyze-button').innerHTML = 'Analyzing...';
  el('result-label').innerHTML = '';
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  xhr.open(
    'POST',
    `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
    true
  );
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
      var response = JSON.parse(e.target.responseText);
      el('result-label').innerHTML = `${response['result']}`;
    }
    el('analyze-button').innerHTML = 'Analyze';
  };

  var fileData = new FormData();
  var content = document.getElementById('input-data').value;
  var blob = new Blob([content], { type: 'text/text' });
  fileData.append('file', blob);
  xhr.send(fileData);
}
