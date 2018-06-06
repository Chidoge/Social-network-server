function checkCode(){

	var codeForm = document.getElementById("codeForm");
    var code = codeForm.elements['code'].value;

    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    }

		xmlhttp.onreadystatechange=function() {

			if (xmlhttp.readyState==4 && xmlhttp.status==200) {

				try {
					var responseText = JSON.parse(xmlhttp.responseText);
					console.log('here ' +responseText.res)
					response = responseText.res;
					if (response == '1') {
						var note = getElementById("incorrect");
						note.innerHTML = 'The code you entered was incorrect, please try again.'
					}
				}
				catch (parseError) {
					console.log('json parse error caught');
				}
			}

		}
	xmlhttp.open("GET","/check_code?code=" + code, true);
	xmlhttp.send();
}