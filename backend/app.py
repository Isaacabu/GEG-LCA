def calculate_co2(area, co2_per_m2):
    total_co2 = area * co2_per_m2
    return total_co2


if __name__ == "__main__":
    area = 120
    co2_per_m2 = 30

    total = calculate_co2(area, co2_per_m2)
    print(f"Gesamter CO2-Wert: {total} kg CO2e")