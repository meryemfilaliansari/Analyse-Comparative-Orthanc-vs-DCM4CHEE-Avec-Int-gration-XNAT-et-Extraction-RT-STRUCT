# -*- coding: utf-8 -*-
"""Correction 2 PACS vs 3 PACS"""

def fix_comparison():
    with open('rapport_complet_optimise.tex', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrections principales
    corrections = {
        "trois solutions PACS": "deux PACS (DCM4CHEE et Orthanc)",
        "trois solutions": "deux PACS",
        "La comparaison des trois": "La comparaison des deux",
        "12 critères": "15+ critères",
        
        # Résumé Exécutif - ligne 297
        "intègre trois solutions PACS open-source majeures": "compare deux solutions PACS open-source majeures — DCM4CHEE et Orthanc — via un frontend interactif. XNAT est intégré séparément pour la recherche clinique et l'anonymisation",
        
        # Supprimer \service{}
        "\\service{DCM4CHEE}, \\service{Orthanc} et \\service{XNAT}": "DCM4CHEE et Orthanc",
        
        # Corrections encodage É
        'É  ': 'à ',
        'É ': 'à ',
    }
    
    count = 0
    for wrong, correct in corrections.items():
        if wrong in content:
            occurrences = content.count(wrong)
            content = content.replace(wrong, correct)
            count += occurrences
            print(f"  ✓ '{wrong[:50]}...' → '{correct[:50]}...' ({occurrences}x)")
    
    with open('rapport_complet_optimise.tex', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ {count} corrections!")
    return count

if __name__ == '__main__':
    print("🔧 Correction comparaison 2 PACS...\n")
    total = fix_comparison()
    print("✅ Rapport corrigé - Comparaison DCM4CHEE vs Orthanc uniquement!")
