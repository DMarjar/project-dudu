#!/bin/bash

# Script para modificar las importaciones antes de los tests y el despliegue

if [ "$1" == "test" ]; then
  # Para cada carpeta (missions, profile, users)
  for module in missions profile users; do
    # Buscar todos los archivos Python y modificar las importaciones
    find modules/$module -name "*.py" -exec sed -i 's/from common/from modules.'"$module"'.\0/g' {} +
  done

elif [ "$1" == "deploy" ]; then
  # Para cada carpeta (missions, profile, users)
  for module in missions profile users; do
    # Restaurar las importaciones originales para el despliegue
    find modules/$module -name "*.py" -exec sed -i 's/from modules.'"$module"'\.\(.*\)\.common/from common/g' {} +
  done
fi
