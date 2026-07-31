(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var modale = document.getElementById('inlineCreateModal');
        if (!modale) return;

        var modalInstance = new bootstrap.Modal(modale);
        var inputNom = document.getElementById('inlineCreateNom');
        var inputUrl = document.getElementById('inlineCreateUrl');
        var inputSelectId = document.getElementById('inlineCreateSelectId');
        var btnSubmit = document.getElementById('inlineCreateBtn');
        var feedback = document.getElementById('inlineCreateFeedback');
        var selectCategorie = document.getElementById('inlineCreateCategorie');

        document.querySelectorAll('[data-inline-create]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                inputSelectId.value = this.getAttribute('data-inline-create');
                inputUrl.value = this.getAttribute('data-url');
                var hasCategorie = this.getAttribute('data-categorie');

                inputNom.value = '';
                feedback.textContent = '';
                feedback.className = 'form-text';

                var catGroup = document.getElementById('inlineCategorieGroup');
                if (hasCategorie && selectCategorie) {
                    catGroup.style.display = 'block';
                    var selectField = document.getElementById(inputSelectId.value);
                    if (selectField && selectField.options.length > 0) {
                        selectCategorie.value = selectField.value || 'AUTRE';
                    }
                } else if (catGroup) {
                    catGroup.style.display = 'none';
                }

                modalInstance.show();
            });
        });

        btnSubmit.addEventListener('click', function() {
            var nom = inputNom.value.trim();
            var url = inputUrl.value;
            var selectId = inputSelectId.value;

            if (!nom) {
                feedback.textContent = 'Veuillez saisir un nom.';
                feedback.className = 'form-text text-danger';
                return;
            }

            var formData = new FormData();
            formData.append('nom', nom);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            if (selectCategorie && selectCategorie.value) {
                formData.append('categorie', selectCategorie.value);
            }

            feedback.textContent = 'Création en cours...';
            feedback.className = 'form-text text-info';

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {'X-Requested-With': 'XMLHttpRequest'},
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.ok) {
                    var select = document.getElementById(selectId);
                    var opt = document.createElement('option');
                    opt.value = data.id;
                    opt.textContent = data.text;
                    select.appendChild(opt);
                    select.value = data.id;
                    select.dispatchEvent(new Event('change'));
                    feedback.textContent = '✓ Créé avec succès.';
                    feedback.className = 'form-text text-success';
                    setTimeout(function() { modalInstance.hide(); }, 800);
                } else {
                    feedback.textContent = data.error || 'Erreur inconnue.';
                    feedback.className = 'form-text text-danger';
                }
            })
            .catch(function(err) {
                feedback.textContent = 'Erreur réseau : ' + err.message;
                feedback.className = 'form-text text-danger';
            });
        });

        function getCookie(name) {
            var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
            return match ? decodeURIComponent(match[2]) : null;
        }
    });
})();
