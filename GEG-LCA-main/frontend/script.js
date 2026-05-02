function calculateEnergy() {
    const area = parseFloat(document.getElementById("area").value);
    const energy = parseFloat(document.getElementById("energy").value);
    const result = document.getElementById("result");

    if (isNaN(area) || isNaN(energy)) {
        result.textContent = "Bitte beide Werte eingeben.";
        return;
    }

    const totalEnergy = area * energy;
    result.textContent = `Gesamtenergiebedarf: ${totalEnergy.toFixed(2)} kWh pro Jahr`;
}