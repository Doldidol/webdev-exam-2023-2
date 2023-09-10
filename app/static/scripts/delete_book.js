let deleteBookModal = document.querySelector('#deleteBook')
deleteBookModal.addEventListener('show.bs.modal', function(event) {
    let form = document.querySelector('form');
    form.action = event.relatedTarget.dataset.url;
    let bookLogin = document.querySelector('#bookLogin');
    bookLogin.innerHTML = event.relatedTarget.closest('.row').querySelector('#bookName').textContent;
});
