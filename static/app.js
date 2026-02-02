/**
 * Wizard navigation and dynamic form logic for "How Much Is Enough?"
 */

document.addEventListener('DOMContentLoaded', () => {
    // =====================================================
    // Step navigation
    // =====================================================
    const steps = document.querySelectorAll('.step-content');
    const progressSteps = document.querySelectorAll('.progress-step');
    const progressLines = document.querySelectorAll('.progress-line');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const calcBtn = document.getElementById('calculate-btn');
    const totalSteps = steps.length;
    let currentStep = 1;

    function showStep(n) {
        // Hide all steps, show the target
        steps.forEach(s => s.classList.remove('active'));
        document.querySelector(`.step-content[data-step="${n}"]`).classList.add('active');

        // Update progress indicators
        progressSteps.forEach((ps, i) => {
            const stepNum = i + 1;
            ps.classList.remove('active', 'completed');
            if (stepNum === n) ps.classList.add('active');
            else if (stepNum < n) ps.classList.add('completed');
        });

        // Update connecting lines
        progressLines.forEach((line, i) => {
            line.classList.toggle('active', i < n - 1);
        });

        // Show/hide nav buttons
        prevBtn.style.visibility = n === 1 ? 'hidden' : 'visible';
        if (n === totalSteps) {
            nextBtn.style.display = 'none';
            calcBtn.style.display = 'inline-flex';
        } else {
            nextBtn.style.display = 'inline-flex';
            calcBtn.style.display = 'none';
        }

        currentStep = n;

        // If landing on step 4, render children forms
        if (n === 4) {
            renderChildren();
        }
    }

    nextBtn.addEventListener('click', () => {
        if (currentStep < totalSteps) showStep(currentStep + 1);
    });
    prevBtn.addEventListener('click', () => {
        if (currentStep > 1) showStep(currentStep - 1);
    });

    // Initialize
    showStep(1);

    // =====================================================
    // Toggle conditional sections
    // =====================================================
    function bindToggle(checkboxId, sectionId) {
        const cb = document.getElementById(checkboxId);
        const section = document.getElementById(sectionId);
        if (!cb || !section) return;

        cb.addEventListener('change', () => {
            section.classList.toggle('visible', cb.checked);
        });
    }

    bindToggle('has_vacation_home', 'vacation-home-section');
    bindToggle('has_sailboat', 'sailboat-section');
    bindToggle('has_yacht', 'yacht-section');
    bindToggle('provide_for_grandchildren', 'gc-details-section');

    // =====================================================
    // Dynamic children forms
    // =====================================================
    const numChildrenSelect = document.getElementById('num_children');
    const childrenContainer = document.getElementById('children-container');
    const grandchildrenSection = document.getElementById('grandchildren-section');

    // Build a location <option> list from the server-injected data
    function locationOptions() {
        return ALL_LOCATIONS.map(
            loc => `<option value="${loc}">${loc}</option>`
        ).join('');
    }

    function childFormHTML(index) {
        return `
        <div class="child-card" data-child="${index}">
            <h4>Child ${index + 1}</h4>
            <div class="form-row">
                <div class="form-group">
                    <label for="child_${index}_age">Current age</label>
                    <input type="number" id="child_${index}_age"
                           name="child_${index}_age"
                           value="5" min="0" max="50" class="input-compact">
                </div>
            </div>

            <div class="form-group toggle-row">
                <span class="toggle-text">Private school (K-12)?</span>
                <label class="toggle">
                    <input type="checkbox" name="child_${index}_private_school"
                           id="child_${index}_private_school" checked>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="form-group toggle-row">
                <span class="toggle-text">Private university?</span>
                <label class="toggle">
                    <input type="checkbox" name="child_${index}_private_university"
                           id="child_${index}_private_university" checked>
                    <span class="slider"></span>
                </label>
            </div>

            <hr class="section-divider">
            <p class="hint" style="margin-bottom:0.75rem">When they're an adult:</p>

            <div class="form-group toggle-row">
                <span class="toggle-text">Buy them a home?</span>
                <label class="toggle">
                    <input type="checkbox" name="child_${index}_buy_house"
                           id="child_${index}_buy_house" checked>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="conditional-section visible" id="child_${index}_house_section">
                <div class="form-row">
                    <div class="form-group">
                        <label for="child_${index}_house_location">Where?</label>
                        <select id="child_${index}_house_location"
                                name="child_${index}_house_location">
                            ${locationOptions()}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="child_${index}_house_bedrooms">Bedrooms?</label>
                        <select id="child_${index}_house_bedrooms"
                                name="child_${index}_house_bedrooms">
                            <option value="2">2</option>
                            <option value="3">3</option>
                            <option value="4" selected>4</option>
                            <option value="5">5</option>
                            <option value="6">6</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label for="child_${index}_annual_expenses">Annual living expenses</label>
                <div class="input-with-prefix">
                    <span class="prefix">$</span>
                    <input type="text" id="child_${index}_annual_expenses"
                           name="child_${index}_annual_expenses"
                           value="300,000" class="input-currency"
                           inputmode="numeric">
                </div>
            </div>
        </div>`;
    }

    function renderChildren() {
        const n = parseInt(numChildrenSelect.value, 10);
        childrenContainer.innerHTML = '';

        for (let i = 0; i < n; i++) {
            childrenContainer.insertAdjacentHTML('beforeend', childFormHTML(i));

            // Bind child house toggle
            const cb = document.getElementById(`child_${i}_buy_house`);
            const section = document.getElementById(`child_${i}_house_section`);
            if (cb && section) {
                cb.addEventListener('change', () => {
                    section.classList.toggle('visible', cb.checked);
                });
            }

            // Format currency in child expense inputs
            const expInput = document.getElementById(`child_${i}_annual_expenses`);
            if (expInput) bindCurrencyFormat(expInput);
        }

        // Show/hide grandchildren section
        grandchildrenSection.style.display = n > 0 ? 'block' : 'none';
    }

    numChildrenSelect.addEventListener('change', renderChildren);

    // =====================================================
    // Currency formatting
    // =====================================================
    function formatCurrency(val) {
        const num = parseInt(val.replace(/[^0-9]/g, ''), 10);
        if (isNaN(num)) return '';
        return num.toLocaleString('en-US');
    }

    function bindCurrencyFormat(input) {
        input.addEventListener('blur', () => {
            input.value = formatCurrency(input.value);
        });
        input.addEventListener('focus', () => {
            input.value = input.value.replace(/,/g, '');
        });
    }

    // Bind formatting to initial currency inputs
    document.querySelectorAll('.input-currency').forEach(bindCurrencyFormat);
});
