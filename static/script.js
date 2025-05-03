function calculerScore(event) {
    event.preventDefault();
    const form = document.getElementById('waterlowForm');
    if (!form) {
        console.error("Formulaire non trouvé !");
        return;
    }
    const formData = new FormData(form);

    let elements = form.elements;
    let score_total = 0;

    for (const [key, value] of formData.entries()) {
        if (WATERLOW_PARAMS.includes(key)) { 
            score_total += parseInt(value) || 0;
        }
    }

    for (let i = 0; i < elements.length; i++) {
        let element = elements[i];

        if (element.tagName === 'SELECT') {
            score_total += parseInt(element.value) || 0;
        }

        if (element.type === 'checkbox' && element.checked) {
            score_total += parseInt(element.value) || 0;
        }
    }

    console.log("Score calculé :", score_total);

    let scoreResult = document.getElementById('scoreResult');
    if (scoreResult) {
        scoreResult.innerHTML = `<h3>Score Total : ${score_total}</h3>`;
        scoreResult.style.color = "#2E7D32";
        scoreResult.style.fontWeight = "bold";
    }

    let recommandations = document.getElementById('recommandations');
    if (!recommandations) {
        console.error("Élément recommandations non trouvé !");
        return;
    }
    recommandations.innerHTML = "";

    let liste = [];

    if (score_total < 10) {
        liste = [
            "Risque faible : Surveillance régulière.",
            "Maintenir une alimentation équilibrée.",
            "Encourager la mobilité."
        ];
    } else if (score_total <= 14) {
        liste = [
            "Risque modéré : Vérification fréquente de la peau.",
            "Utilisation d'un matelas en mousse.",
            "Hydratation adéquate."
        ];
    } else if (score_total <= 19) {
        liste = [
            "Risque élevé : Surveillance rapprochée.",
            "Changement de position toutes les 2-3 heures.",
            "Utilisation de coussins de décharge."
        ];
    } else {
        liste = [
            "Risque très élevé : Matelas à air motorisé.",
            "Repositionnement toutes les 2 heures.",
            "Consultation spécialisée recommandée."
        ];
    }

    liste.forEach(rec => {
        let li = document.createElement('li');
        li.textContent = rec;
        recommandations.appendChild(li);
    });
}
document.querySelectorAll("button").forEach(btn => {
    btn.style.fontWeight = "bold";
});
