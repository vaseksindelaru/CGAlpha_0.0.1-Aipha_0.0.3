# scripts/deterministic_patch_bug1.py

from pathlib import Path

TARGET_FILE = Path("cgalpha_v3/lila/llm/oracle.py")

# Cambio 1: añadir import
OLD_IMPORT = "from sklearn.preprocessing import LabelEncoder"
NEW_IMPORT = "from sklearn.preprocessing import LabelEncoder\nfrom sklearn.model_selection import train_test_split"

# Cambio 2: reemplazar el bloque fit + score con split + fit + test score
OLD_FIT_BLOCK = """        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X, y)

        train_accuracy = float(self.model.score(X, y))"""

NEW_FIT_BLOCK = """        # BUG-1 fix: separar train/test para métricas OOS reales
        if len(X) >= 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            # Dataset muy pequeño: sin split para no perder datos
            X_train, X_test, y_train, y_test = X, X, y, y

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X_train, y_train)

        train_accuracy = float(self.model.score(X_train, y_train))
        test_accuracy = float(self.model.score(X_test, y_test))"""

# Cambio 3: añadir test_accuracy a las métricas
OLD_METRICS = """        self._training_metrics = {
            "n_samples": int(len(X)),
            "train_accuracy": round(train_accuracy, 4),"""

NEW_METRICS = """        self._training_metrics = {
            "n_samples": int(len(X)),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "train_accuracy": round(train_accuracy, 4),
            "test_accuracy": round(test_accuracy, 4),"""


def apply_fix():
    print(f"Reading {TARGET_FILE}...")
    content = TARGET_FILE.read_text()

    changes = [
        (OLD_IMPORT,   NEW_IMPORT,   "import train_test_split"),
        (OLD_FIT_BLOCK, NEW_FIT_BLOCK, "fit block con split"),
        (OLD_METRICS,  NEW_METRICS,  "métricas con test_accuracy"),
    ]

    for old, new, label in changes:
        if old not in content:
            print(f"❌ FALLO: No encontré '{label}' en el archivo.")
            print(f"   Fragmento buscado: {repr(old[:80])}")
            return False
        content = content.replace(old, new, 1)
        print(f"✅ Aplicado: {label}")

    TARGET_FILE.write_text(content)
    print(f"\n✅ BUG-1 fix aplicado en {TARGET_FILE}")
    return True


if __name__ == "__main__":
    apply_fix()
