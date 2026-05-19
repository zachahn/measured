class RakeTaskFailure
  attr_accessor :task_name
  attr_accessor :path
  attr_accessor :message

  def self.all
    @failures ||= []
  end

  def self.create(...)
    all.push(new(...))
  end

  def initialize(task_name, path, message)
    self.task_name = task_name
    self.path = path
    self.message = message
  end
end

at_exit do
  RakeTaskFailure.all.each do |f|
    puts "==> #{f.path}"
    puts "--> #{f.message}"
  end
end

module TestTasks
  extend Rake::DSL

  task :test do
    require "yaml"

    Dir.glob("source/skills/**/SKILL.md").each do |path|
      check_name("test", path, File.basename(File.dirname(path)))
    rescue => e
      RakeTaskFailure.create("test", path, e.message)
      next
    end

    Dir.glob("source/agents/*.md").each do |path|
      check_name("test", path, File.basename(path, ".md"))
    rescue => e
      RakeTaskFailure.create("test", path, e.message)
      next
    end

    sh "python3 test/test_note_lib.py"
    sh "python3 test/test_agenda_lib.py"

    puts "[test] done"
  end

  def self.check_name(task_name, path, expected_name)
    content = File.read(path)
    unless content.start_with?("---\n")
      RakeTaskFailure.create(task_name, path, "Missing YAML frontmatter")
      return
    end

    _, frontmatter, _ = content.split(/^---\s*$/, 3)
    frontmatter = YAML.load(frontmatter)

    actual_name = frontmatter["name"]

    if actual_name.nil?
      RakeTaskFailure.create(task_name, path, "Missing `name` in frontmatter")
    elsif actual_name != expected_name
      RakeTaskFailure.create(task_name, path, "Name `#{actual_name}` does not match expected `#{expected_name}`")
    end
  end

  def self.check_description(task_name, path)
    content = File.read(path)
    unless content.start_with?("---\n")
      RakeTaskFailure.create(task_name, path, "Missing YAML frontmatter")
      return
    end

    _, frontmatter, _ = content.split(/^---\s*$/, 3)
    frontmatter = YAML.load(frontmatter)

    actual_description = frontmatter["description"]

    if actual_description.nil?
      RakeTaskFailure.create(task_name, path, "Missing `description`")
    end
  end
end

module BuildTasks
  extend Rake::DSL

  def self.partials(path)
    @partials ||= {}
    @partials[path] ||= File.read(File.join("source/_partials", path))
  end

  def self.root
    Pathname.new(__dir__)
  end

  task :build do
    require "erb"
    require "fileutils"
    require "pathname"

    Dir.glob("source/**/*").each do |source|
      dest = source.sub(%r{\Asource/}, "")
      destdir = File.dirname(dest)
      next if dest == source
      next if File.directory?(source)
      next if source.start_with?("source/_")

      original = File.read(source)
      erb = ERB.new(original)
      built = erb.result(binding)

      FileUtils.mkdir_p(destdir)
      File.write(dest, built)
    rescue => e
      RakeTaskFailure.create(:build, source, e.message)
      next
    end

    puts "[build] done"
  end
end

module VersionTasks
  extend Rake::DSL

  CONFIG_PATH = ".version-bump.json"

  def self.repo_root
    @repo_root ||= File.expand_path(__dir__)
  end

  def self.config
    require "json"
    @config ||= JSON.parse(File.read(File.join(repo_root, CONFIG_PATH)))
  end

  def self.declared_files
    config["files"].map { |entry| [entry["path"], entry["field"]] }
  end

  def self.audit_excludes
    (config.dig("audit", "exclude") || []) + [".git", "node_modules"]
  end

  # Walk a dotted field path like "plugins.0.version" through a parsed JSON
  # structure. Numeric segments index into arrays, others into hashes.
  def self.field_path(field)
    field.split(".").map { |seg| seg.match?(/\A\d+\z/) ? Integer(seg) : seg }
  end

  def self.read_field(file, field)
    require "json"
    data = JSON.parse(File.read(file))
    field_path(field).each do |seg|
      data = data[seg]
    end
    data
  end

  def self.write_field(file, field, value)
    require "json"
    data = JSON.parse(File.read(file))
    path = field_path(field)
    target = path[0..-2].inject(data) { |acc, seg| acc[seg] }
    target[path.last] = value
    File.write(file, JSON.pretty_generate(data) + "\n")
  end

  def self.check
    has_drift = false
    versions = []

    puts "Version check:"
    puts ""

    declared_files.each do |path, field|
      fullpath = File.join(repo_root, path)
      unless File.file?(fullpath)
        printf("  %-45s  MISSING\n", "#{path} (#{field})")
        has_drift = true
        next
      end
      ver = read_field(fullpath, field)
      printf("  %-45s  %s\n", "#{path} (#{field})", ver)
      versions << ver
    end

    puts ""

    unique = versions.uniq
    if unique.size > 1
      puts "DRIFT DETECTED — versions are not in sync:"
      versions.tally.sort_by { |_v, c| -c }.each do |ver, count|
        puts "  #{ver} (#{count} files)"
      end
      has_drift = true
    else
      puts "All declared files are in sync at #{versions.first}"
    end

    !has_drift
  end

  def self.current_version
    counts = Hash.new(0)
    declared_files.each do |path, field|
      fullpath = File.join(repo_root, path)
      next unless File.file?(fullpath)
      counts[read_field(fullpath, field)] += 1
    end
    counts.max_by { |_v, c| c }&.first
  end

  # Walk the repo to find any file (outside the exclude list) containing the
  # given version string. Returns an array of "relpath:lineno:line" matches.
  def self.scan_for_version(version)
    excludes = audit_excludes
    declared = declared_files.map(&:first).to_set
    matches = []

    Dir.glob(File.join(repo_root, "**", "*"), File::FNM_DOTMATCH).each do |path|
      next unless File.file?(path)
      rel = path.sub("#{repo_root}/", "")

      next if excludes.any? { |ex| rel == ex || rel.start_with?("#{ex}/") || File.basename(rel) == ex }
      next if declared.include?(rel)

      begin
        content = File.read(path, encoding: "UTF-8")
      rescue ArgumentError, Errno::EISDIR
        next
      end
      next unless content.valid_encoding?
      next unless content.include?(version)

      content.each_line.with_index(1) do |line, lineno|
        matches << "#{rel}:#{lineno}:#{line.chomp}" if line.include?(version)
      end
    end

    matches
  end

  def self.audit
    require "set"
    check
    puts ""

    version = current_version
    if version.nil? || version.empty?
      warn "error: could not determine current version"
      return false
    end

    puts "Audit: scanning repo for version string '#{version}'..."
    puts ""

    matches = scan_for_version(version)

    if matches.empty?
      puts "No undeclared files contain the version string. All clear."
    else
      puts "UNDECLARED files containing '#{version}':"
      matches.each { |m| puts "  #{m}" }
      puts ""
      puts "Review the above files — if they should be bumped, add them to .version-bump.json"
      puts "If they should be skipped, add them to the audit.exclude list."
    end

    true
  end

  def self.bump(new_version)
    unless new_version =~ /\A\d+\.\d+\.\d+/
      abort "error: '#{new_version}' doesn't look like a version (expected X.Y.Z)"
    end

    puts "Bumping all declared files to #{new_version}..."
    puts ""

    declared_files.each do |path, field|
      fullpath = File.join(repo_root, path)
      unless File.file?(fullpath)
        puts "  SKIP (missing): #{path}"
        next
      end
      old_ver = read_field(fullpath, field)
      write_field(fullpath, field, new_version)
      printf("  %-45s  %s -> %s\n", "#{path} (#{field})", old_ver, new_version)
    end

    puts ""
    puts "Done. Running audit to check for missed files..."
    puts ""
    audit

    puts ""
    puts "Staging and committing version bump..."
    declared_files.each do |path, _field|
      fullpath = File.join(repo_root, path)
      sh "git", "-C", repo_root, "add", path if File.file?(fullpath)
    end
    sh "git", "-C", repo_root, "commit", "-m", "Release v#{new_version}"
  end

  namespace :version do
    desc "Show current versions, detect drift"
    task :check do
      exit 1 unless VersionTasks.check
    end

    desc "Check + scan repo for undeclared version references"
    task :audit do
      VersionTasks.audit
    end

    desc "Bump all declared files to NEW_VERSION (rake version:bump NEW_VERSION=1.2.3)"
    task :bump do
      new_version = ENV["NEW_VERSION"] || ENV["VERSION"]
      abort "Usage: rake version:bump NEW_VERSION=X.Y.Z" if new_version.nil? || new_version.empty?
      VersionTasks.bump(new_version)
    end
  end
end

task default: [:test, :build]
