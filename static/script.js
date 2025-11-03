let index = 0;
let startTime = 0;

function startStudy(trials, worker_id, condition) {

    loadTrial();

    function loadTrial() {
        if (index >= trials.length) {
            window.location.href = "/complete";
            return;
        }

        const t = trials[index];
        startTime = performance.now();

        document.getElementById("task").innerHTML = `
            <h3>Article ${index + 1} of ${trials.length}</h3>
            <b>Headline:</b> ${t.title}<br>
            <b>Description:</b> ${t.text}<br>
            <b>Date:</b> ${t.date}<br><br>

            <button onclick="submitResponse('REAL')">Real</button>
            <button onclick="submitResponse('FAKE')">Fake</button>
            <br><br>

            Confidence (0 = guess, 100 = certain):
            <input type="number" id="conf" min="0" max="100" value="50"><br><br>

            ${condition === "assisted" ? '<button onclick="getAI()">Get AI Suggestion</button>' : ''}
            <p id="ai_output"></p>
        `;

        window.getAI = function() {
            fetch("/predict", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({title: t.title, text: t.text})
            })
            .then(res => res.json())
            .then(data => {
                window.ai_label = data.label;
                window.ai_conf = data.confidence;
                document.getElementById("ai_output").innerHTML =
                  `<b>AI Suggestion:</b> ${data.label} (${data.confidence}%)`;
            });
        };

        window.submitResponse = function(label) {
            const endTime = performance.now();
            const response_time = Math.round(endTime - startTime);
            const confidence = document.getElementById("conf").value;

            const truth = String(t.label).toLowerCase();

            const isCorrect = (
                (label === 'REAL' && truth === 'true') ||
                (label === 'FAKE' && truth !== 'true')
            );

            // Disable only the Real/Fake buttons
            document.querySelectorAll("#task button").forEach(btn => btn.disabled = true);

            // Show feedback + "Next" button
            document.getElementById("task").innerHTML += `
                <p style="font-weight:bold; color:${isCorrect ? 'green' : 'red'};">
                    ${isCorrect ? "Correct!" : `Incorrect — It was actually ${truth.toUpperCase()}`}
                </p>
                <button id="nextBtn">Next</button>
            `;

            const payload = {
                worker_id,
                condition,
                trial_id: index,
                title: t.title,
                text: t.text,
                date: t.date,
                ground_truth: t.label,
                human_label: label,
                ai_label: window.ai_label || null,
                ai_confidence: window.ai_conf || null,
                response_time,
                confidence_rating: confidence
            };

            fetch("/submit_trial", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            // Attach handler for "Next" button AFTER it's added
            document.getElementById("nextBtn").onclick = function() {
                window.ai_label = null;
                window.ai_conf = null;
                index++;
                loadTrial();
            };
        };
    }
}
