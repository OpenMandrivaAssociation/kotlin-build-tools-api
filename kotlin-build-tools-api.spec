Name:		kotlin-build-tools-api
Version:	2.4.21
Release:	1
Summary:	Kotlin build tools API
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/JetBrains/kotlin
# Kotlin tag v2.4.21. Sources are compiler/build-tools/kotlin-build-tools-api
# src/main plus the tag's checked-in gen/ arguments. jdk-utils is the small
# project upstream embeds into this jar.
Source0:	kotlin-build-tools-api-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)

%description
org.jetbrains.kotlin:kotlin-build-tools-api %{version}.
Compiler build-tools interfaces from Kotlin v2.4.21, compiled with the
installed kotlinc 2.0.21. The JDK class-loader helpers upstream embeds
are compiled into the same jar.

%prep
%autosetup -n kotlin-build-tools-api-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
CPSTD=%{_javadir}/kotlin-stdlib.jar
test -s "$CPSTD"
mkdir -p classes
find jdk-utils -name '*.kt' > utils.list
test "$(wc -l < utils.list)" -eq 2
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-cp "$CPSTD" -d classes @utils.list
test -s classes/org/jetbrains/kotlin/buildtools/internal/KotlinBuildToolsInternalJdkUtils.class
find src/main gen -name '*.kt' > sources.list
test "$(wc -l < sources.list)" -eq 112
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-Xjvm-default=all \
	-opt-in=org.jetbrains.kotlin.buildtools.internal.KotlinBuildToolsInternalJdkUtils \
	-cp "$CPSTD:classes" -d classes @sources.list
test -s classes/org/jetbrains/kotlin/buildtools/api/KotlinReleaseVersion.class
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: kotlin.buildtools.api' > manifest.mf
jar cfm kotlin-build-tools-api.jar manifest.mf -C classes .
jar i kotlin-build-tools-api.jar
desc=$(jar --describe-module --file kotlin-build-tools-api.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'kotlin.buildtools.api automatic'
cat > kotlin-build-tools-api.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains.kotlin</groupId>
  <artifactId>kotlin-build-tools-api</artifactId>
  <version>%{version}</version>
  <name>kotlin-build-tools-api</name>
  <description>Kotlin build tools API</description>
  <url>https://github.com/JetBrains/kotlin</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>2.0.21</version>
    </dependency>
  </dependencies>
</project>
END


%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact kotlin-build-tools-api.pom:kotlin-build-tools-api.jar \
	--file-name kotlin-build-tools-api \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.jetbrains.kotlin/kotlin-build-tools-api.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "kotlin-build-tools-api"' "$idx"
test -s %{buildroot}%{_javadir}/kotlin-build-tools-api.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/kotlin-build-tools-api.jar
test -s "$JAR"
STDLIB=%{_javadir}/kotlin-stdlib.jar
mkdir -p check
cat > check/ReleaseVer.kt << 'EOF'
import org.jetbrains.kotlin.buildtools.api.KotlinReleaseVersion

fun main() {
    val version = KotlinReleaseVersion(2, 4, 21)
    val older = KotlinReleaseVersion(2, 0, 21)
    if (version.compareTo(older) <= 0) error("compare")
    if (version.toString() != "2.4.21") error("string")
    println("kotlin_build_tools_api_ok " + version.toString())
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-cp "$JAR:$STDLIB" -d check/out check/ReleaseVer.kt
java -cp "check/out:$JAR:$STDLIB" ReleaseVerKt > check/out.txt
cat check/out.txt
grep -F -qx 'kotlin_build_tools_api_ok 2.4.21' check/out.txt

%files -f .mfiles
%license LICENSE.txt
%doc NOTICE.txt
