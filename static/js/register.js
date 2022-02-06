const username = document.querySelector('#id_username');

cuser = false;
cmail = false;

function checkSubmit() {
    if (cuser && cmail) {
        submitbtn.removeAttribute('disabled');
    } else {
        submitbtn.setAttribute("disabled", 'disabled');
    }

}

username.addEventListener("keyup", (e) => {
    const usernameVal = e.target.value;
    console.log('username', usernameVal)
    id_username.classList.remove('is-invalid');
    id_username.classList.remove('is-valid');
    if (usernameVal.length > 0) {
        fetch("/validate-username", {
            body: JSON.stringify({ username: usernameVal }),
            method: "POST",
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.username_error) {
                    console.log(data)
                    id_username.classList.add('is-invalid');
                    cuser = false;

                }
                else {
                    id_username.classList.add('is-valid');
                    cuser = true;

                }
            });
    }

});

const email = document.querySelector('#email_register');
email.addEventListener("keyup", (e) => {
    const emailVal = e.target.value;
    email_register.classList.remove('is-invalid');
    email_register.classList.remove('is-valid');
    if (emailVal.length > 0) {
        fetch('/validate-email', {
            body: JSON.stringify({ email: emailVal }),
            method: "POST",
        })
            .then((res) => res.json())
            .then((data) => {
                console.log(data)
                if (data.email_error) {
                    email_register.classList.add('is-invalid');
                    cmail = false;
                }
                else {
                    email_register.classList.add('is-valid');
                    cmail = true;

                }
            });
    }
});