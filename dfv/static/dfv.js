window.getCsrfTokenCookie = function () {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue ?? "n/a";
}

function addCsrfTokenHeader(event) {
    event.detail.headers['X-CSRFToken'] = getCsrfTokenCookie();
}

document.body.addEventListener('htmx:configRequest', addCsrfTokenHeader);

document.body.addEventListener("fetch:beforeRequest", addCsrfTokenHeader);

window.parse_element = function (elementId) {
    return JSON.parse(document.getElementById(elementId).textContent)
}

/**
 * @param {HTMLElement} el
 */
// function liveErrors(el) {
//     let parent = el;
//
//     /** @type {null | HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement} */
//     let control = null;
//
//     // find control
//     while (control == null && parent != null) {
//         control = parent.querySelector("input")
//                 || parent.querySelector("select")
//                 || parent.querySelector("textarea");
//
//         parent = parent.parentElement;
//     }
//
//     if (control == null) {
//         return;
//     }
//     let className = control.className;
//     let dirty = false;
//
//     // find form
//     /** @type {null | HTMLFormElement} */
//     let form = null;
//     while (form == null && parent != null) {
//         if (parent instanceof HTMLFormElement) {
//             form = parent;
//         }
//         parent = parent.parentElement;
//     }
//
//     if (form == null) {
//         return;
//     }
//
//     let url = form.getAttribute("hx-post")
//             || form.getAttribute("action")
//             || window.location.toString();
//
//     if (url == null || url === "") {
//         return;
//     }
//
//     // event: input
//     let debounceTimeout = null;
//     control.addEventListener("input", function (event) {
//         dirty = true;
//         clearTimeout(debounceTimeout);
//         debounceTimeout = setTimeout(function () {
//             handleInput();
//         }, 250);
//     });
//
//     // event: blur
//     control.addEventListener("blur", function () {
//         handleInput();
//     });
//
//     function handleInput() {
//         if (!dirty) {
//             return;
//         }
//
//         clearTimeout(debounceTimeout);
//
//         let data = Object.fromEntries(new FormData(form));
//
//         let controlName = control.getAttribute("name");
//         fetch(url, {
//             method: "PATCH",
//             headers: {
//                 "X-CSRFToken": getCsrfTokenCookie(),
//                 "Content-Type": "application/json; charset=utf-8",
//                 "X-DFV-Validate-Field": controlName,
//             },
//             body: JSON.stringify(data),
//         }).then(function (result) {
//             result.text().then(function (text) {
//                 let result = JSON.parse(text);
//                 const field_result = result.fields[controlName];
//                 let classes = field_result.attrs["class"]
//                 if (classes == null) {
//                     classes = "";
//                 }
//                 el.innerHTML = field_result.errors;
//                 control.className = className + " " + classes;
//             });
//         });
//     }
// }
